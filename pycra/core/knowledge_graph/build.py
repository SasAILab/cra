import re
from typing import Union
from collections import Counter, defaultdict

from pycra import settings
from pycra.core.document_processing import chunk_documents, Chunk
from pycra.core.knowledge_graph.graph_store import BaseGraphStorage, NetworkXStorage, neo4j_importer
from pycra.core.templates.kg import KG_EXTRACTION_PROMPT, KG_SUMMARIZATION_PROMPT
from pycra.utils.common import (
    detect_main_language, pack_history_conversations,
    split_string_by_multi_markers, handle_single_entity_extraction,
    handle_single_relationship_extraction, compute_content_hash,
    time_record
)
from pycra.core.llm_server import BaseLLMClient
from pycra.utils.run_concurrent import run_concurrent
from pycra.core.knowledge_graph.models import *
from pycra.utils.logger import cckg_logger

class KgBuilder:
    """
    Entity and relation extraction module based on LLM.
    Uses structured prompting to extract entities and relationships from contract content.
    """
    
    def __init__(self, llm_pycra: BaseLLMClient = None):
        self.logger = cckg_logger
        self.llm_pycra = llm_pycra
        self.max_loop = settings.kg.max_loop

    # local_perception_recognition
    async def local_perception_recognition(self, chunk: Chunk) -> Tuple[Dict[str, List[dict]], Dict[Tuple[str, str], List[dict]]]:
        """
        Main method to extract entities and relationships from contract content.
        
        Args:
            chunk: Chunk of contract Object
            chunk.content = contract_content: Preprocessed contract content
            chunk.id = contract_id: Optional unique identifier for the contract
            
        Returns:
            Dictionary containing extracted entities, relationships, and metadata
        """
        contract_content = chunk.content
        contract_id = chunk.id
        self.logger.info(f"Starting entity and relation extraction from id=:{contract_id}")
        if not contract_content:
            self.logger.error("No contract content provided for extraction")
            raise ValueError("Contract content must be provided")
        language = detect_main_language(contract_content)
        try:
            # TODO few-shot 的例子 要经典 后续业务数据有badcase的可以人工调整后作为few-shot
            hint_prompt = KG_EXTRACTION_PROMPT[language]["TEMPLATE"].format(
                    **KG_EXTRACTION_PROMPT["FORMAT"], input_text=contract_content,
                    entity_types=ENTITY_LIST, entity_types_des=ENTITY_DES)
            hint_prompt_token_count = self.llm_pycra.tokenizer.count_tokens(hint_prompt)
            self.logger.debug(f"the hint prompt token size: \n {hint_prompt_token_count}")
            # initial glean
            final_result = await self.llm_pycra.generate_answer(hint_prompt)
            self.logger.debug("init result: %s", final_result)

            # iterative refinement
            history = pack_history_conversations(hint_prompt, final_result)
            self.logger.debug(f"the history: \n {history}")
            for loop_idx in range(self.max_loop):
                if_loop_result = await self.llm_pycra.generate_answer(
                text=KG_EXTRACTION_PROMPT[language]["IF_LOOP"], history=history
            )
                if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
                if if_loop_result != "yes":
                    break

                glean_result = await self.llm_pycra.generate_answer(
                    text=KG_EXTRACTION_PROMPT[language]["CONTINUE"], history=history
                )
                self.logger.debug("Loop %s glean: %s", loop_idx + 1, glean_result)

                history += pack_history_conversations(
                    KG_EXTRACTION_PROMPT[language]["CONTINUE"], glean_result
                )
                final_result += glean_result
            self.logger.debug(f"loop after final_result: \n {final_result}")
            # step 4: parse the final result
            records = split_string_by_multi_markers(
                final_result,
                [
                    KG_EXTRACTION_PROMPT["FORMAT"]["record_delimiter"],
                    KG_EXTRACTION_PROMPT["FORMAT"]["completion_delimiter"],
                ],
            )
            self.logger.debug(f"the records: \n {records}")
            nodes = defaultdict(list)
            edges = defaultdict(list)

            for record in records:
                match = re.search(r"\((.*)\)", record)
                if not match:
                    continue
                inner = match.group(1)

                attributes = split_string_by_multi_markers(
                    inner, [KG_EXTRACTION_PROMPT["FORMAT"]["tuple_delimiter"]]
                )

                entity = await handle_single_entity_extraction(attributes, chunk.id)
                if entity is not None:
                    nodes[entity["entity_name"]].append(entity)
                    continue

                relation = await handle_single_relationship_extraction(attributes, chunk.id)
                if relation is not None:
                    key = (relation["src_id"], relation["tgt_id"])
                    edges[key].append(relation)
            self.logger.debug(f"the nodes: \n {nodes} \n the edges: \n {edges}")
        except Exception as e:
            self.logger.error(f"Entity and relation extraction failed: {e}", exc_info=True)
            raise
        return dict(nodes), dict(edges)

    async def merge_nodes(
        self,
        node_data: tuple[str, List[dict]],
        kg_instance: BaseGraphStorage,
    ) -> None:
        entity_name, node_data = node_data
        entity_types = []
        source_ids = []
        descriptions = []

        node = await kg_instance.get_node(entity_name)
        if node is not None:
            entity_types.append(node["entity_type"])
            source_ids.extend(
                split_string_by_multi_markers(node["source_id"], ["<SEP>"])
            )
            descriptions.append(node["description"])
        entity_type = sorted(
            Counter([dp["entity_type"] for dp in node_data] + entity_types).items(),
            key=lambda x: x[1],
            reverse=True,
        )[0][0]

        description = "<SEP>".join(
            sorted(set([dp["description"] for dp in node_data] + descriptions))
        )
        description = await self._handle_kg_summary(entity_name, description, max_summary_tokens=settings.kg.max_summary_tokens)

        source_id = "<SEP>".join(
            set([dp["source_id"] for dp in node_data] + source_ids)
        )

        node_data = {
            "entity_type": entity_type,
            "description": description,
            "source_id": source_id,
        }
        await kg_instance.upsert_node(entity_name, node_data=node_data)

    async def merge_edges(
        self,
        edges_data: tuple[Tuple[str, str], List[dict]],
        kg_instance: BaseGraphStorage,
    ) -> None:
        (src_id, tgt_id), edge_data = edges_data

        source_ids = []
        descriptions = []

        edge = await kg_instance.get_edge(src_id, tgt_id)
        if edge is not None:
            source_ids.extend(
                split_string_by_multi_markers(edge["source_id"], ["<SEP>"])
            )
            descriptions.append(edge["description"])

        description = "<SEP>".join(
            sorted(set([dp["description"] for dp in edge_data] + descriptions))
        )
        source_id = "<SEP>".join(
            set([dp["source_id"] for dp in edge_data] + source_ids)
        )

        for insert_id in [src_id, tgt_id]:
            if not await kg_instance.has_node(insert_id):
                await kg_instance.upsert_node(
                    insert_id,
                    node_data={
                        "source_id": source_id,
                        "description": description,
                        "entity_type": "UNKNOWN",
                    },
                )

        description = await self._handle_kg_summary(
            f"({src_id}, {tgt_id})", description, max_summary_tokens=settings.kg.max_summary_tokens
        )

        await kg_instance.upsert_edge(
            src_id,
            tgt_id,
            edge_data={"source_id": source_id, "description": description},
        )

    async def _handle_kg_summary(
        self,
        entity_or_relation_name: str,
        description: str,
        max_summary_tokens: int = 200,
    ) -> str:
        """
        Handle knowledge graph summary

        :param entity_or_relation_name
        :param description
        :param max_summary_tokens
        :return summary
        """

        tokenizer_instance = self.llm_pycra.tokenizer
        language = detect_main_language(description)
        if language == "en":
            language = "English"
        else:
            language = "Chinese"
        KG_EXTRACTION_PROMPT["FORMAT"]["language"] = language

        tokens = tokenizer_instance.encode(description)
        if len(tokens) < max_summary_tokens:
            return description

        use_description = tokenizer_instance.decode(tokens[:max_summary_tokens])
        prompt = KG_SUMMARIZATION_PROMPT[language]["TEMPLATE"].format(
            entity_name=entity_or_relation_name,
            description_list=use_description.split("<SEP>"),
            **KG_SUMMARIZATION_PROMPT["FORMAT"],
        )
        new_description = await self.llm_pycra.generate_answer(prompt)
        self.logger.info(
            "Entity or relation %s summary: %s",
            entity_or_relation_name,
            new_description,
        )
        return new_description


    async def _split_chunks(self, md_content: str, contract_id: str) -> List[Chunk]:
        new_docs = {
            compute_content_hash(md_content, prefix="md-"): {
                "content": md_content
            }
        }
        inserting_chunks = await chunk_documents(
            new_docs,
            settings.kg.chunk_size,
            settings.kg.chunk_overlap,
            self.llm_pycra.tokenizer,
            text_id=contract_id
        )
        inserting_chunks = {
            k: v for k, v in inserting_chunks.items()
        }
        chunks = [
            Chunk(id=k, content=v["content"]) for k, v in inserting_chunks.items()
        ]
        return chunks

    @time_record
    async def build_graph(self, md_content: Optional[str] = None, contract_id: Optional[str] = None) -> Tuple[
        list[tuple[str, dict]],
        list[tuple[str, str, dict]],
        str
    ]:
        """
        Extract entities and relationships from contract sections individually,
        then merge the results.
        
        Args:
            md_content: str --> the contract raw content of the ocr
            contract_id: Optional unique identifier for the contract
            
        Returns:
            Dictionary containing merged extracted entities, relationships, and metadata
        """
        self.logger.info(f"Starting extract entity and relation for {contract_id} contract_id")
        """
        # core1: 提取实体和关系的时候 要有全局视角 --> 假设第一章和第二章之间的某个实体之间有关联 这种情况 这个实体-关系-实体就必须被挖掘出来
        
        # core2: 如果合同太大 大几十页甚至几百页的情况 --> 如何挖掘出来所有的实体和关系 保证没有遗漏呢? 另外，LLM上下文溢出怎么处理? 
        
        # core3: 实体模型的定义和关系模型的定义 --> 要不断的根据业务badcase来迭代
        
        # core4: 实体和关系提取的准确性保证 --> loop模块+few shot解决遗漏和准确性的问题
        
        # core5: 速度保证 --> llm后端使用vllm/lmdeploy服务 chunks采用一个线程池 局部强召回的时候把全部chunks并发出去 全局再聚合到一起处理
        """
        # TODO 图的质量保证 --> GraphGen的judge模块 来计算loss
        # TODO 图谱的评估指标, 一个高质量的图谱对后续的任务是非常重要的 -->https://deepwiki.com/open-sciencelab/GraphGen/9.2-knowledge-graph-evaluation || https://deepwiki.com/open-sciencelab/GraphGen/9.3-confidence-calculation-and-metrics#yesno-loss-metrics
        """
        图谱评估指标
            指标	描述	质量指标
            total_nodes	图中的节点总数	图表大小
            total_edges	图中的边总数	图密度
            noise_ratio	孤立节点与总节点数的比率	越低越好（< 0.15）
            largest_cc_ratio	最大连通分量的大小/节点总数	数值越高越好（> 0.90）
            avg_degree	所有节点的平均节点度	应该在 [2.0, 5.0] 范围内 --> 节点的度数是指与该节点直接相连的边的数量
            powerlaw_r2	度分布幂律拟合的 R² 值	数值越高越好（> 0.75） --> 度分布：统计图中不同度数（k）的节点数量分布 --> 幂律分布：很多真实网络（社交网络、互联网等）的度分布遵循 P(k) ∝ k^(-γ) 的规律,即少数节点有很多连接（hub节点）, 多数节点只有少量连接 --> R² 值含义: 衡量度分布符合幂律的程度 R² ∈ [0, 1]，越接近1表示拟合越好
            is_robust	布尔值，指示是否满足所有阈值	通过/失败指示器
        """

        # step1: Chapter divisions for md_content
        init_chunks = await self._split_chunks(md_content, contract_id)
        # step2: Local Extraction --> 局部强召回 这一步的目标是“宁可错杀，不可放过”, 在小范围内，尽可能多地把所有潜在的实体和关系都找出来。
        results = await run_concurrent(
            self.local_perception_recognition,
            init_chunks,
            desc="[2/4]Extracting entities and relationships from chunks",
            unit="chunk",
        )
        namespace_postfix = compute_content_hash(md_content)
        namespace = f"{settings.kg.namespace}_{contract_id}_{namespace_postfix}"
        kg_instance = NetworkXStorage(
            settings.kg.working_dir, namespace=namespace
        )
        # step3: 全局拓扑对齐 --> 将不同文本块中抽取的同一个实体统一成一个全局ID。
        nodes = defaultdict(list)
        edges = defaultdict(list)
        for n, e in results:
            for k, v in n.items():
                nodes[k].extend(v)
            for k, v in e.items():
                edges[tuple(sorted(k))].extend(
                    v)
        await run_concurrent(
            lambda kv: self.merge_nodes(kv, kg_instance=kg_instance),
            list(nodes.items()),
            desc="Inserting entities into storage",
        )
        await run_concurrent(
            lambda kv: self.merge_edges(kv, kg_instance=kg_instance),
            list(edges.items()),
            desc="Inserting relationships into storage",
        )
        g = await kg_instance.get_graph()
        file_name = f"{settings.kg.working_dir}/{namespace}.graphml"
        NetworkXStorage.write_nx_graph(graph=g, file_name=file_name)
        return_nodes = await kg_instance.get_all_nodes()
        return_egdes = await kg_instance.get_all_edges()

        return return_nodes, return_egdes, namespace

if __name__ == "__main__":
    import os

    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    from pycra.core.llm_server import LLMFactory
    import asyncio
    llm_pycra = LLMFactory.create_llm_cli()
    builder = KgBuilder(llm_pycra)
    md_content = """
# 系统开发合同

项目名称：基于区块链的开发区政务大数据平台建设项目

甲方：北京经济技术开发区管理委员会信息化工作办公室

乙方：深圳奇迹智慧网络有限公司

签订时间：2019年06月19日

签订地点：北京经济技术开发区

甲乙双方依照《中华人民共和国合同法》、《中华人民共和国建筑法》及其他有关法律、行政法规及政府规章的规定，在平等、自愿、公平和诚实信用的原则的基础上，就甲方委托乙方进行基于区块链的开发区政务大数据平台项目事宜经协商达成一致，订立本合同，以兹共同遵守。本合同“甲方”、“乙方”单独称为一方，合称为“双方”。

# 一、标的技术的内容、范围及要求

1、软件系统：即基于区块链的开发区政务大数据平台软件系统，是乙方根据本合同约定的项目需求开发的软件产品。（项目需求详见附件1）  
2、软件系统实施：软件系统实施是指乙方依据本合同约定的项目需求，按照约定的项目实施计划（见第三条款）进行软件系统设计、开发、测试，以及软件系统完成后的安装、维护工作。

# 3、技术成果：

（1）软件系统安装盘、可执行程序光盘  
（2）技术文档：1）实施方案

（2）需求分析说明书  
3）详细设计方案  
4）数据库设计说明书  
5）系统部署安装方案  
6）系统测试方案  
7）系统测试用例  
8）系统测试报告  
9）第三方软件测试报告  
10）信息安全测评报告  
11）项目建设总结报告  
12）用户操作手册  
13）系统运行维护方案  
14）其他相关资料和文件

4、乙方完成项目建设内容后，认为系统功能和技术指标达到合同要求，可向甲方提出项目初验申请；初验合格后进入试运行，试运行期3个月；系统通过试运行后，进行竣工验收。

项目竣工验收申请。  
5、系统开发地点：北京经济技术开发区。  
6、系统验收地点：北京经济技术开发区。

# 二、应达到的技术指标和参数

乙方提交给甲方的技术成果应满足本合同约定的项目需求。（项目需求详见附件1）

# 三、研究开发计划

项目开发周期为90个日历天，上线后试运行周期为90个日历天，合计整体项目交付周期为180个日历天。

# 四、研究开发经费、报酬及其支付结算方式

1、本合同总价合计为¥8595000.00元(大写金额:捌佰伍拾玖万伍仟元整)。(价格明细见附件2)。

# 2、付款方式

本合同具体付款方式如下：

(1) 合同双方签订后, 甲方在收到乙方提供的正规发票后十五个工作日内, 甲方向乙方支付合同款的 15%, 即壹佰贰拾捌万九千二百五十元整人民币 (¥1289250.00 元)。  
(2) 项目初验合格后, 甲方在收到乙方提供的正规发票后十五个工作日内, 向乙方支付至合同款的 45%, 即叁佰捌拾陆万柒仟柒佰伍拾元整人民币 (¥3867750.00 元)。  
(3) 项目终验合格后, 甲方在收到乙方提供的正规发票后十五个工作日内, 甲方向乙方支付合同款的 30%, 即贰佰伍拾柒万捌仟伍佰元整人民币 (￥2578500.00元)。  
(4) 系统免费维护期结束后, 甲方在收到乙方提供的正规发票后十五个工作日内, 向乙方支付合同款的 10%, 即捌拾伍万玖仟伍佰元整人民币 (¥859500.00 元)。

# 五、服务和培训

1、乙方为本项目系统软件提供两年的免费维护，免费维护期自本项目终验合格之日起开始计算。  
2、在免费维护期内，乙方应按照本合同第一款第3条中所提及的“系统运行维护方案”进行维护，并在任何时候收到甲方通知系统故障后24小时内派人解决问题。  
3、乙方根据本合同第一款第3条中所提及的“培训方案”，及时委派技术人员对甲方进行相应的软件系统培训。

# 六、需求变更

1、在本合同履行过程中，甲方要求进行需求变更和乙方建议进行需求变更时，均需经双方同意并采用书面形式进行确认。在双方未就需求变更达成一致，未进行书面形式确认之前，乙方应继续履行其义务，视同双方未要求或未提议进行需求变更。

2、项目需求变更后，如果乙方工作量减少或增加幅度在乙方全部工作量的 $10\%$ 以内的，甲方无需相应减少或增加应向乙方支付的费用；如乙方工作量减少或增加幅度大于该比例的，双方应就相应减少或增加费用进行协商，并签署相应的书面补充协议。  
3、本合同生效后，如果发生以下情况：增加新的功能、系统结构发生重大变动、对已确定的系统功能进行重大修改等，经甲乙双方确认后，可视为重大需求变更。此类变更超出本次项目的开发内容，甲乙双方应另行进行新的商务谈判，按新项目进行协商并签署新项目书面协议。

4、因项目需求发生变化而导致项目不能在预定的时间进行验收的，不属于乙方违约，乙方不承担任何包括违约责任和损害赔偿责任在内的一切法律责任。

# 七、合同履行的期限、地点和方式

本合同自合同双方签字盖章之日起在北京经济技术开发区履行，有效期3年。

本合同的履行方式：

本软件系统实施在北京经济技术开发区进行，乙方利用甲方的软硬件环境完成软件全部设计、开发、测试工作任务。本软件系统开发完成后到最终用户指定的地点进行现场安装调试和运维。

# 八、技术情报和资料的保密

1、通过本项目，乙方所掌握的与甲方有关的技术资料、商业秘密、原始数据等信息，未经甲方书面同意或许可，乙方不得向任何第三方披露，否则甲方有权要求乙方支付违约金，并赔偿由此给甲方造成的损失。  
2、双方均对对方提供的技术情报、资料等承担保密义务，不论本合同是否变更、解除、终止，本条款长期有效。

本条款对以下内容不适用：

1)提供时已为公众所知，属于常识的内容；  
2)已通过出版物或其它原因（未经授权行为或疏忽除外）而为公众所知，成为常识的内容；  
3)由任何第三方未加限制提供的内容，且该第三方对这些内容无任何明示或暗示的保密义务；  
4)按法律要求须向任何机关、机构公开的内容。

# 九、技术协作和技术指导的内容

# 1、甲方的基本权利和义务

（1）甲方负责向乙方提供与本软件系统有关的资料、文件，以及为乙方在实施过程中对甲方所进行的调研、实施工作进行配合。  
（2）甲方须在本软件系统的设计、开发前，在乙方的配合下确定具体的项目需求。  
（3）保证本软件系统的使用应当符合国家法律规定和社会公共利益；  
（4）对乙方提供与本合同有关的资料等负有保密的责任。  
（5）按本合同的约定向乙方支付费用；  
（6）甲方主动配合接受开发区结果查究工作。

# 2、乙方的基本权利和义务

（1）按照本合同约定的项目需求、项目实施计划、质量要求等完成软件系统的设计、开发、测试，及安装、培训工作，并保证该软件系统的功能符合本合同的约定。  
（2）乙方保证按照项目实施计划要求及时派出合格的技术人员提供准确、充足的技术服务及合同约定的技术培训，确保软件系统实施工作的正常进展。  
（3）乙方保证所提供的软件系统为技术上先进的、品质优异的全新产品，适用于本合同所提及的目的和用途。

（4）乙方保证所提供的技术文档的完整、清晰和准确，满足本合同的要求。  
（5）保证所提供软件系统的内容符合国家法律规定和社会公共利益；  
（6）对甲方提供与本合同有关的资料等负有保密的责任。  
（7）乙方向甲方保证乙方实施人员的稳定性，如在项目实施过程中乙方项目经理发生人员变化，需提前一个月通知甲方，否则按乙方违约处理。  
（8）乙方应按照《开发区信息化项目管理办法》实施系统开发工作，接受开发区中小型电子政务项目集中式监理的统一监督、管理。  
（9）乙方主动配合接受开发区结果查究工作。

# 十、技术成果的归属和分享

1、甲方对于按本合同要求开发的软件享有著作权。  
2、所有资料，包括但不限于甲方交给乙方的文件、图样等保密信息，其所有权应由甲方保有。  
3、乙方所开发的软件应不涉及版权纠纷，如因乙方开发的软件导致版权纠纷，由此给甲方带来得任何损失由乙方承担。  
4、使用在软件系统中的乙方原有的技术成果，乙方仍然享有其著作权。

# 十一、验收的标准和方式

# （一）系统初验

1、系统安装开始前，乙方应按合同约定的项目需求完成软件开发工作，并经演示取得甲方对软件内容功能和质量的当面认可，甲方认可后开始系统安装工作，甲方准备好设备安装现场的各项安装条件。  
2、初验的程序和验收标准：乙方在完成软件系统安装工作，并对甲方系统测试人员进行培训后，应以书面申请形式通知甲方进行验收，同时提供下列资料：

（1）测试方案  
（2）系统测试用例  
（3）用户操作手册  
（4）其他相关资料和文件

甲方在收到乙方提交的书面验收申请通知后15日内，组织专家对项目工作量、报价和系统运行情况进行论证验收，并出具初验报告。乙方应当配合甲方对信息系统使用人员进行测试指导，验收内容包括：

（1）软件系统工作范围应符合合同约定的项目需求，具有已确定的所有功能。  
（2）软件系统所有功能应符合通常标准，即能够使甲方操作人员正常简便使用这些功能，并具较好的容错性。  
（3）软件系统初步具备稳定性，数据表现形式符合规范。  
（4）信息系统数据处理是否正确。  
（5）信息系统性能是否满足业务要求。  
（6）系统报价合理性。

甲方在进行以上检验后，确定验收结果。若验收合格，由甲方在乙方提供的验收报告上签字确认后生效。若确实乙方所提供的软件系统不能满足验收要求，乙方应在5日内修正后与甲方进一步进行验收。

3、若由于乙方原因未能在合同约定时间完成验收，则视为乙方违约，按第十三条款第1条执行。

# （二）系统试运行

1、项目通过初步验收后进入系统试运行环节，乙方应当确定试运行范围、设定试运行目标，制定各方协调机制和试运行计划，组织相关的业务人员开展试运行。乙方应当制定系统维护方案、培训计划和培训教材。  
2、乙方应当进行系统试运行环境准备，部署信息系统，开展业务人员系统使用培训，在试运行期间提供技术支持并跟踪系统试运行情况。  
3、系统试运行业务人员重点验证在真实的业务环境中，系统的稳定性和可用性，是否符合业务需求、业务流程要求、数据处理和存储要求，对于试运行期间出现的各项问题予以记录并提出系统改进意见，形成业务人员试运行反馈意见。  
4、乙方应当按照业务人员试运行反馈意见修改系统、完善系统功能、优化系统性能。甲方再次组织业务人员开展试运行评价。  
5、项目达到试运行目标后，甲乙双方共同签字确认形成项目试运行评价意见。

# （三）竣工验收

1、信息系统通过试运行后，乙方应当提交验收申请及验收方案，同时提交下列资料：

（1）实施方案  
（2）需求分析说明书  
（3）详细设计方案  
（4）数据库设计说明书  
（5）系统部署安装方案  
（6）系统测试方案  
（7）系统测试用例  
（8）系统测试报告  
（9）第三方软件测试报告  
（10）信息安全测评报告  
（11）项目建设总结报告  
（12）用户操作手册  
（13）系统运行维护方案  
（14）其他相关资料和文件

2、甲方接到乙方的竣工验收申请后，应当在15日内组织开发区管委会信息办及专家评审并形成专家验收意见，同时形成甲方、乙方、管委会信息办共同签字确认的项目竣工验收意见。验收不合格不得投入使用，甲方出具整改意见交乙方，限期整改完成后再进行验收。自验收合格之日起，系统进入正式运行期，乙方提供为期两年的免费

系统维护。

# 十二、风险责任的承担

1、如果在各方合作期间发生不可抗力（指无法预见、不可避免的事件，例如：地震、台风、战争、火灾、水灾、并非因违反劳动合同而引起的罢工、政府行为及政府禁令），致使一方不能履行或延迟履行其在本合同项下的全部或部分义务，则遭受该不可抗力的一方不承担违约责任和损害赔偿责任。  
2、遇上述不可抗力事件的一方，应及时将不可抗力事件情况按照本合同说明的联系方式24小时内通知另一方，并在一周内提供事件详情及不能履行其在本合同项下的全部或部分义务的理由的有效文件，上述通知与文件应由事件发生地政府主管部门出具或经公证机构出具公证证明，双方应立即协商寻找合理办法，并尽一切努力减轻不可抗力的后果。  
3、在不可抗力发生后及其持续期间，各方应尽其可能继续履行其在本合同项下的义务，乙方应在出现这种情况期间保护和确保项目实施安全。乙方应向甲方建议在此期间可采取的措施。  
4、所有本合同要求发出的或按照本合同发出的所有通知、要求、同意和其他文件应采用书面形式并以当面递交或传真方式发送至对方。

# 十三、违约责任

1、如由乙方原因未能按照合同约定如期完成约定工作，乙方则应向甲方支付违约金。违约金为每延期一日支付本合同款的 $1.0\%$ 以上违约金总额不得超过本合同款的 $50\%$ 。支付以上违约金后，乙方仍对本合同所需的服务有继续交货的义务；乙方违约逾期超过90天，甲方有权中止本合同。

# 十四、法律适用及争议的解决

1、本合同的订立、效力、解释、履行及其争议的解决，均适用中华人民共和国法律。  
2、甲乙双方在合同履行过程中发生的一切争议，均应通过双方友好协商解决。如果协商开始之日起三十（30）日内未能达成一致意见，协商不成的，合同双方中任何一方均可以将争议诉讼至原告方住所地方人民法院解决。  
3、当产生任何争议及任何争议正在诉讼期间，除争议事项外，双方应继续行使其剩余的相关权利，履行其本协议项下的其他义务。  
4、在仲裁或诉讼期间，双方均应继续执行本合同除有争议的部分以外的其它部分。

# 十五、定义和解释

本合同中使用的下述词汇或用语，除非合同上下文另有要求，否则应具有下面所赋予它们的涵义：

1、“本合同”指甲乙双方之间签订的基于区块链的开发区政务大数据平台开发合同及其全部附件。  
2、“软件系统”是指基于区块链的开发区政务大数据平台。  
3、“附件”指本合同所列出的全部附件，为本合同不可分割的部分，任何提及“本合同”之处均包括附件。

4、免费维护期：是指乙方为甲方提供的免费维护本软件系统的时间。  
5、计算机程序：指为了得到某种结果而可以由计算机等具有信息处理能力的装置执行的代码化指令序列，或者可被自动转换成代码化指令序列的符号化指令序列或者符号化语句序列。  
6、技术文档：指用自然语言或者形式化语言所编写的文字资料和图表，用来描述该项目的内容、组成、设计、功能规格、开发情况、测试结果及使用方法，如软件需求说明书、用户手册等。  
7、本合同及附件经甲乙双方确认后，形成项目开发“基准”。项目的开发以此“基准”为依据开展工作。在项目的开发过程中甲乙双方均可提出对“基准”的修改，经甲乙双方共同以合同附件的形式(签字并盖章)确认后形成有效的“变更”，与其它未更改的“基准”一起，作为乙方开发和验收的标准。

# 十六、遵守法律、法规及规章

各方应遵守所有与本合同有关的实施、验收、维护等有关的国家或地方的法律、法规及规章。一方若违反上述法律、法规及规章，应由该方承担相应的法律责任。

# 十七、其它

本合同包括附件两份，附件为本合同有效组成部分。本合同及附件壹式陆份，甲乙双方各执叁份，合同及附件具有同等法律效力，本合同经甲乙双方代表签字、盖章后生效。若有未尽事宜，须经双方共友好协商解决并签订补充协议，补充协议与本合同具有同等法律效力。

附件1：《基于区块链的开发区政务大数据平台项目实施方案》

附件2：《基于区块链的开发区政务大数据平台项目报价清单》

![](images/8cad807129b20b755353bb08b987ae83fa8455dc4c002e27eb69d8067440537a.jpg)

![](images/b62682df10ee721427e07a0c4a434c0d4906430163a2a408bd4750fb21a24a84.jpg)
    """
    contract_id = "27"
    result = asyncio.run(builder.build_graph(md_content, contract_id))