# pylint: disable=C0301
TEMPLATE_EN: str = """You are an NLP expert, skilled at analyzing text to extract named entities and their relationships.

-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.
Use English as output language.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text. If English, capitalized the name.
- entity_type: One of the following types: [{entity_types}]
- entity_summary: Comprehensive summary of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_summary>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_summary: explanation as to why you think the source entity and the target entity are related to each other
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_summary>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

################
-Examples-
################
-Example 1-
Text:
################
In the second century of the Christian Era, the empire of Rome comprehended the fairest part of the earth, and the most civilized portion of mankind. The frontiers of that extensive monarchy were guarded by ancient renown and disciplined valor. The gentle but powerful influence of laws and manners had gradually cemented the union of the provinces. Their peaceful inhabitants enjoyed and abused the advantages of wealth and luxury. The image of a free constitution was preserved with decent reverence: the Roman senate appeared to possess the sovereign authority, and devolved on the emperors all the executive powers of government. During a happy period of more than fourscore years, the public administration was conducted by the virtue and abilities of Nerva, Trajan, Hadrian, and the two Antonines.
################
Output:
("entity"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"organization"{tuple_delimiter}"The dominant empire of the second century CE, encompassing the most developed regions of the known world."){record_delimiter}
("entity"{tuple_delimiter}"Second Century CE"{tuple_delimiter}"date"{tuple_delimiter}"Time period of the Christian Era when the Roman Empire was at its height."){record_delimiter}
("entity"{tuple_delimiter}"Rome"{tuple_delimiter}"location"{tuple_delimiter}"The capital and heart of the Roman Empire."){record_delimiter}
("entity"{tuple_delimiter}"Roman Senate"{tuple_delimiter}"organization"{tuple_delimiter}"Legislative body that appeared to hold sovereign authority in Rome."){record_delimiter}
("entity"{tuple_delimiter}"Nerva"{tuple_delimiter}"person"{tuple_delimiter}"Roman emperor who contributed to the public administration during a prosperous period."){record_delimiter}
("entity"{tuple_delimiter}"Trajan"{tuple_delimiter}"person"{tuple_delimiter}"Roman emperor known for his virtue and administrative abilities."){record_delimiter}
("entity"{tuple_delimiter}"Hadrian"{tuple_delimiter}"person"{tuple_delimiter}"Roman emperor who governed during the empire's peaceful period."){record_delimiter}
("entity"{tuple_delimiter}"Antonines"{tuple_delimiter}"person"{tuple_delimiter}"Two Roman emperors who ruled during a period of prosperity and good governance."){record_delimiter}
("entity"{tuple_delimiter}"Roman Law"{tuple_delimiter}"concept"{tuple_delimiter}"System of laws and manners that unified the provinces of the Roman Empire."){record_delimiter}
("relationship"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"Roman Law"{tuple_delimiter}"The empire was unified and maintained through the influence of its laws and customs."){record_delimiter}
("relationship"{tuple_delimiter}"Roman Senate"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"The Senate appeared to possess sovereign authority while delegating executive powers to emperors."){record_delimiter}
("relationship"{tuple_delimiter}"Nerva"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"Nerva was one of the emperors who contributed to the empire's successful administration."){record_delimiter}
("relationship"{tuple_delimiter}"Trajan"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"Trajan was one of the emperors who governed during the empire's prosperous period."){record_delimiter}
("relationship"{tuple_delimiter}"Hadrian"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"Hadrian was one of the emperors who managed the empire's administration effectively."){record_delimiter}
("relationship"{tuple_delimiter}"Antonines"{tuple_delimiter}"Roman Empire"{tuple_delimiter}"The Antonines were emperors who helped maintain the empire's prosperity through their governance."){record_delimiter}
("content_keywords"{tuple_delimiter}"Roman governance, imperial prosperity, law and order, civilized society"){completion_delimiter}

-Example 2-
Text:
#############
Overall, the analysis of the OsDT11 sequence demonstrated that this protein belongs to the CRP family. Since OsDT11 is predicted to be a secreted protein, the subcellular localization of OsDT11 was determined by fusing the OsDT11 ORF to RFP in a p35S::RFP vector by in vivo protein targeting in NB epidermal cells by performing an Agrobacterium tumefaciens-mediated transient assay. After incubation for 48 h, the RFP signals were mainly detected in the cell-wall of OsDT11-RFP transformed cells, while the control cells (transformed with the RFP construct) displayed ubiquitous RFP signals, demonstrating that OsDT11 is a secreted signal peptide. Moreover, when the infiltrated leaf sections were plasmolyzed, the OsDT11-RFP fusion proteins were located on the cell wall.
#############
Output:
("entity"{tuple_delimiter}"OsDT11"{tuple_delimiter}"gene"{tuple_delimiter}"A protein sequence belonging to the CRP family, demonstrated to be a secreted signal peptide that localizes to cell walls."){record_delimiter}
("entity"{tuple_delimiter}"CRP family"{tuple_delimiter}"science"{tuple_delimiter}"A protein family to which OsDT11 belongs, characterized by specific structural and functional properties."){record_delimiter}
("entity"{tuple_delimiter}"RFP"{tuple_delimiter}"technology"{tuple_delimiter}"Red Fluorescent Protein, used as a fusion marker to track protein localization in cells."){record_delimiter}
("entity"{tuple_delimiter}"p35S::RFP vector"{tuple_delimiter}"technology"{tuple_delimiter}"A genetic construct used for protein expression and visualization studies, containing the 35S promoter and RFP marker."){record_delimiter}
("entity"{tuple_delimiter}"NB epidermal cells"{tuple_delimiter}"nature"{tuple_delimiter}"Plant epidermal cells used as the experimental system for protein localization studies."){record_delimiter}
("entity"{tuple_delimiter}"Agrobacterium tumefaciens"{tuple_delimiter}"nature"{tuple_delimiter}"A bacteria species used for transferring genetic material into plant cells in laboratory experiments."){record_delimiter}
("relationship"{tuple_delimiter}"OsDT11"{tuple_delimiter}"CRP family"{tuple_delimiter}"OsDT11 is identified as a member of the CRP family through sequence analysis."){record_delimiter}
("relationship"{tuple_delimiter}"OsDT11"{tuple_delimiter}"RFP"{tuple_delimiter}"OsDT11 was fused to RFP to study its cellular localization."){record_delimiter}
("relationship"{tuple_delimiter}"Agrobacterium tumefaciens"{tuple_delimiter}"NB epidermal cells"{tuple_delimiter}"Agrobacterium tumefaciens was used to transfer genetic material into NB epidermal cells through a transient assay."){record_delimiter}
("relationship"{tuple_delimiter}"OsDT11"{tuple_delimiter}"NB epidermal cells"{tuple_delimiter}"OsDT11's subcellular localization was studied in NB epidermal cells, showing cell wall targeting."){record_delimiter}
("content_keywords"{tuple_delimiter}"protein localization, gene expression, cellular biology, molecular techniques"){completion_delimiter}

################
-Real Data-
################
Entity_types: {entity_types}
Text: {input_text}
################
Output:
"""

TEMPLATE_ZH: str = """您是一位专业的NLP合同分析专家，擅长从法律文件中分析文本提取命名实体和关系

-目标-
给定一个实体类型列表和可能与列表相关的文本，从文本中识别所有这些类型的实体，以及这些实体之间所有的关系。
使用中文作为输出语言。

-实体类型的中文解释-
{entity_types_des}

-步骤-
1. 识别所有实体。对于每个识别的实体，提取以下信息：
   - entity_name：实体的名称，首字母大写
   - entity_type：以下类型之一：[{entity_types}]
   - entity_summary：实体的属性与活动的全面总结
   将每个实体格式化为("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_summary>)

2. 从步骤1中识别的实体中，识别所有（源实体，目标实体）对，这些实体彼此之间*明显相关*。
   对于每对相关的实体，提取以下信息：
   - source_entity：步骤1中识别的源实体名称
   - target_entity：步骤1中识别的目标实体名称
   - relationship_summary：解释为什么你认为源实体和目标实体彼此相关
   将每个关系格式化为("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_summary>)

3. 以中文返回步骤1和2中识别出的所有实体和关系的输出列表。使用**{record_delimiter}**作为列表分隔符。

4. 完成后，输出{completion_delimiter}

################
-示例-
################
-示例 1-
文本：
################
# 解除劳动合同通知书先生/小姐根据 $< <$ 劳动合同法 $> >$ 相关规定，公司依法解除此前您与公司订立的劳动合同(合同期限:年 月 日至 年 月 日)。解除您的理由是：# （1）过失性解除口在试用期内证明不符合录用条件的； 口严重违反公司依法制定的规章制度的；口严重失职，营私舞弊，给用人单位造成重大损害的；口以欺诈、胁迫的手段使用人单位违背真实意思签订劳动合同致使劳动合同无效的；口员工同时与其他用人单位建立劳动关系，对完成本单位的工作任务造成严重影响，或者经用人单位提出，拒不改正的； 口被依法追究刑事责任的；# （2）非过失性解除口劳动合同订立时所依据的客观情况发生重大变化，致使原合同无法履行，经当事人协商不能就变更合同达成协议的；口员工不能胜任工作，经过培训或者调整工作岗位，仍不能胜任的；口员工患病或非因工负伤，医疗期满后不能从事原工作，也不能从事由公司安排的其他工作；
################
输出：
("entity"{tuple_delimiter}公司{tuple_delimiter}ContractParty"{tuple_delimiter}作为劳动合同的一方主体，即用人单位，依法提出解除与员工订立的劳动合同。){record_delimiter}
("entity"{tuple_delimiter}员工{tuple_delimiter}ContractParty"{tuple_delimiter}作为劳动合同的另一方主体，即劳动者，是被公司通知解除劳动合同的对象。){record_delimiter}
("entity"{tuple_delimiter}劳动合同{tuple_delimiter}Contract{tuple_delimiter}是公司与员工之间订立的、期限为指定年 月 日至 年 月 日的协议，现被公司依法解除。){record_delimiter}
("entity"{tuple_delimiter}解除{tuple_delimiter}RightObligation{tuple_delimiter}指公司根据《劳动合同法》规定所行使的单方面终止合同的权利和行为。){record_delimiter}
("entity"{tuple_delimiter}《劳动合同法》{tuple_delimiter}Condition{tuple_delimiter}是本次解除劳动合同行为所依据的法律规定和前提条件。){record_delimiter}
("entity"{tuple_delimiter}劳动合同订立时所依据的客观情况发生重大变化{tuple_delimiter}Condition{tuple_delimiter}是非过失性解除合同的一种法定条件，指致使原合同无法履行的客观变化。){record_delimiter}
("entity"{tuple_delimiter}严重违反公司依法制定的规章制度{tuple_delimiter}BreachClause{tuple_delimiter}是可能导致过失性解除劳动合同的具体违约行为之一。){record_delimiter}
("entity"{tuple_delimiter}严重失职，营私舞弊，给用人单位造成重大损害{tuple_delimiter}BreachClause{tuple_delimiter}是可能导致过失性解除劳动合同的具体违约行为之一。){record_delimiter}
("entity"{tuple_delimiter}在试用期内证明不符合录用条件{tuple_delimiter}BreachClause{tuple_delimiter}是可能导致过失性解除劳动合同的具体条件之一。){record_delimiter}
("entity"{tuple_delimiter}年 月 日至 年 月 日{tuple_delimiter}DateTerm{tuple_delimiter}是合同中约定的原始合同期限。){record_delimiter}
("entity"{tuple_delimiter}试用期{tuple_delimiter}TimeSpan{tuple_delimiter}是劳动合同中的一个特定阶段，在此期间若员工不符合录用条件可被解除合同。){record_delimiter}
("entity"{tuple_delimiter}医疗期{tuple_delimiter}TimeSpan{tuple_delimiter}指员工患病或非因工负伤后依法享有的治疗和休息期限，期满后不能从事原工作可能触发非过失性解除。){record_delimiter}
("entity"{tuple_delimiter}其他用人单位{tuple_delimiter}Organization{tuple_delimiter}指员工可能同时与之建立劳动关系的其他组织，此行为可能构成过失性解除的理由。){record_delimiter}
("entity"{tuple_delimiter}过失性解除{tuple_delimiter}BreachClause{tuple_delimiter}是解除劳动合同的一种类型，基于员工的过错行为，如严重违纪、严重失职等。){record_delimiter}
("entity"{tuple_delimiter}非过失性解除{tuple_delimiter}BreachClause{tuple_delimiter}是解除劳动合同的一种类型，基于非因员工过错的客观情况，如客观情况重大变化、员工不胜任工作等。){record_delimiter}
("entity"{tuple_delimiter}客观情况发生重大变化{tuple_delimiter}Condition{tuple_delimiter}是导致非过失性解除的具体情形，使得原劳动合同无法继续履行。){record_delimiter}
("entity"{tuple_delimiter}不能胜任工作{tuple_delimiter}Condition{tuple_delimiter}是导致非过失性解除的一种员工能力状态，即使经过培训或调岗仍无法满足工作要求。){record_delimiter}
("entity"{tuple_delimiter}患病或非因工负伤{tuple_delimiter}Condition{tuple_delimiter}是员工的一种健康状况，在医疗期满后可能触发非过失性解除。){record_delimiter}
("entity"{tuple_delimiter}培训{tuple_delimiter}RightObligation{tuple_delimiter}在员工不能胜任工作时，用人单位有义务提供培训，这也是解除前的一个法定步骤。){record_delimiter}
("entity"{tuple_delimiter}调整工作岗位{tuple_delimiter}RightObligation{tuple_delimiter}在员工不能胜任原工作时，用人单位可以或需要为其调整工作岗位，是解除前的替代方案。){record_delimiter}
("entity"{tuple_delimiter}协商{tuple_delimiter}RightObligation{tuple_delimiter}在客观情况发生重大变化导致合同无法履行时，双方有协商变更合同的义务，协商不成方可解除。){record_delimiter}
("entity"{tuple_delimiter}规章制度{tuple_delimiter}Condition{tuple_delimiter}公司依法制定的、员工必须遵守的行为准则，严重违反之可作为解除合同的依据。){record_delimiter}
("entity"{tuple_delimiter}重大损害{tuple_delimiter}Amount{tuple_delimiter}指因员工严重失职、营私舞弊给用人单位造成的严重经济损失或负面影响的程度描述。){record_delimiter}
("entity"{tuple_delimiter}欺诈、胁迫{tuple_delimiter}BreachClause{tuple_delimiter}员工使用不正当手段致使劳动合同无效的具体过错行为。){record_delimiter}
("entity"{tuple_delimiter}劳动合同无效{tuple_delimiter}Condition{tuple_delimiter}因欺诈、胁迫等手段导致合同自始没有法律约束力的状态，可作为解除的理由。){record_delimiter}
("entity"{tuple_delimiter}被依法追究刑事责任{tuple_delimiter}BreachClause{tuple_delimiter}员工因犯罪行为被司法机关定罪处罚，构成过失性解除的严重情形。){record_delimiter}
("relationship"{tuple_delimiter}公司{tuple_delimiter}员工{tuple_delimiter}公司是劳动合同的甲方（用人单位），员工是乙方（劳动者），双方是合同的直接相对方。){record_delimiter}
("relationship"{tuple_delimiter}公司{tuple_delimiter}劳动合同{tuple_delimiter}公司是与员工订立该劳动合同的一方主体，该合同明确了双方的权利义务。){record_delimiter}
("relationship"{tuple_delimiter}员工{tuple_delimiter}劳动合同{tuple_delimiter}员工是与公司订立该劳动合同的另一方主体，受该合同条款约束。){record_delimiter}
("relationship"{tuple_delimiter}公司{tuple_delimiter}解除{tuple_delimiter}公司作为主体，依法行使解除劳动合同的权利（义务），是解除行为的发起方。){record_delimiter}
("relationship"{tuple_delimiter}解除{tuple_delimiter}劳动合同{tuple_delimiter}解除是作用于劳动合同上的行为，其直接结果是终止该合同的有效性。){record_delimiter}
("relationship"{tuple_delimiter}解除{tuple_delimiter}《劳动合同法》{tuple_delimiter}解除行为的法律依据是《劳动合同法》，该法律规定了解除的条件和程序。){record_delimiter}
("relationship"{tuple_delimiter}解除{tuple_delimiter}严重违反公司依法制定的规章制度{tuple_delimiter}员工的此类违约行为是触发公司行使过失性解除权的具体条件之一。){record_delimiter}
("relationship"{tuple_delimiter}解除{tuple_delimiter}劳动合同订立时所依据的客观情况发生重大变化{tuple_delimiter}此种客观条件的变化是触发公司行使非过失性解除权的具体条件之一。){record_delimiter}
("relationship"{tuple_delimiter}劳动合同{tuple_delimiter}年 月 日至 年 月 日{tuple_delimiter}该时间段是劳动合同中明确约定的合同有效期限。){record_delimiter}
("relationship"{tuple_delimiter}劳动合同{tuple_delimiter}试用期{tuple_delimiter}试用期是包含在劳动合同期限内的一个特定阶段，其规则由劳动合同约定及法律规定。){record_delimiter}
("relationship"{tuple_delimiter}员工{tuple_delimiter}其他用人单位{tuple_delimiter}员工可能同时与其他用人单位建立劳动关系，此行为是对原劳动合同履行义务的违反，构成解除理由。){record_delimiter}
("relationship"{tuple_delimiter}过失性解除{tuple_delimiter}严重违反公司依法制定的规章制度{tuple_delimiter}严重违反规章制度是构成过失性解除的一个具体理由和子类别。){record_delimiter}
("relationship"{tuple_delimiter}过失性解除{tuple_delimiter}在试用期内证明不符合录用条件{tuple_delimiter}试用期不符合录用条件是构成过失性解除的一个具体理由和子类别。){record_delimiter}
("relationship"{tuple_delimiter}非过失性解除{tuple_delimiter}客观情况发生重大变化{tuple_delimiter}客观情况发生重大变化是构成非过失性解除的一个具体理由和子类别。){record_delimiter}
("relationship"{tuple_delimiter}非过失性解除{tuple_delimiter}不能胜任工作{tuple_delimiter}员工不能胜任工作是构成非过失性解除的一个具体理由和子类别。){record_delimiter}
("relationship"{tuple_delimiter}公司{tuple_delimiter}规章制度{tuple_delimiter}公司是规章制度的制定主体，规章制度约束员工行为。){record_delimiter}
("relationship"{tuple_delimiter}不能胜任工作{tuple_delimiter}培训{tuple_delimiter}当员工出现不能胜任工作的情况时，公司有提供培训的义务，作为解除前的补救措施。){record_delimiter}
("relationship"{tuple_delimiter}不能胜任工作{tuple_delimiter}调整工作岗位{tuple_delimiter}当员工不能胜任原工作时，调整工作岗位是公司可以采取的另一种补救措施。){record_delimiter}
("relationship"{tuple_delimiter}客观情况发生重大变化{tuple_delimiter}协商{tuple_delimiter}当发生客观情况重大变化时，双方必须先就变更合同进行协商，这是法定的前置程序。){record_delimiter}
("relationship"{tuple_delimiter}严重失职，营私舞弊，给用人单位造成重大损害{tuple_delimiter}重大损害{tuple_delimiter}重大损害是评价员工严重失职、营私舞弊行为后果严重程度的标准。){record_delimiter}
("relationship"{tuple_delimiter}欺诈、胁迫{tuple_delimiter}劳动合同无效{tuple_delimiter}员工的欺诈、胁迫行为是导致劳动合同无效的直接原因。){completion_delimiter}
-示例 2-
文本：
################
# 录用通知书亲爱的 李子茉 同学：感谢您对公司的认可，我们非常高兴地邀请您加入山东亿云信息技术有限公司，热忱的欢迎您成为亿云大家庭的一员，我们相信公司能够给您提供一个长期发展和成长的机会，更期盼您在亿云平台上充分发挥个人的智慧与才能。我们邀请您担任的初始职位为： 人工智能工程师 。您在公司的进一步发展将取决于公司的发展、您的个人绩效、能力和意愿。您入职所须知晓相关事项如下：49．在您取得毕业证前处于实习期；取得毕业证后为您办理入职手续，您的劳动合同期限为三年，试用期为六个月；试用期后将根据您试用期间指标成绩，确定是否转正，您本人完全接受公司的安排；  50．实习期间，无法为您缴纳社会保险及公积金；您取得毕业证并办理入职手续后，公司将为您缴纳社会保险及公积金（10日前当月缴纳，10日后次月缴纳）；  51．您的薪资：实习期硕士研究生工资标准为 150元/天，本科工资标准为 120元/天；试用期工资标准为（ 9600 元/月)；转正工资标准为：( 12000 元/月)。年终奖根据公司及事业部经营情况确定；  52．工作时间为：周一至周五 8:30-17:30 或 9:00-18:00，午休 70 分钟；  53．您的福利为：实习期电脑补贴 100 元/月，无餐补；试用期电脑补贴 100 元/月，餐补 150 元/月，节假日福利；  54．您转正后的福利为：在试用期福利基础上，增加通讯补贴、带薪年假等；  55．公司实行严格的薪酬保密制，请您对您的薪资标准进行严格保密，违者将解除劳动关系；  56．因工作需要，请您携带笔记本电脑；  57．根据公司用人要求，签订正式劳动合同人员需满足无违法犯罪记录，无重大失信记录（证明材料详见签订正式劳动合同携带材料 8、9、11项），存在相关违法犯罪记录或重大失信记录人员，公司有权不予录用；  58．加入亿云后，公司要求您遵守公司的一切有关政策和规定；您不允许为其它公司做兼职工作或从事与本公司利益发生冲突的商业活动；  59．实习期（未毕业）报到时请携带：（1）居民身份证原件及复印件（正反面复印在一张 A4 纸，彩印）；  （2）中国招商银行卡原件及复印件（正反面复印在一张 A4纸）；  （3）学生证原件及复印件（封皮、信息页复印在一张 A4 纸）。# 60．签订正式劳动合同时请携带：
################
输出：
("entity"{tuple_delimiter}李子茉{tuple_delimiter}Person{tuple_delimiter}本录用通知书的接收者，应聘人工智能工程师职位的自然人。){record_delimiter}
("entity"{tuple_delimiter}山东亿云信息技术有限公司{tuple_delimiter}ContractParty{tuple_delimiter}发出本录用通知书的用人单位，即合同的甲方/雇主方，文中简称为"公司"或"亿云"。){record_delimiter}
("entity"{tuple_delimiter}人工智能工程师{tuple_delimiter}ProductService{tuple_delimiter}李子茉被邀请担任的初始职位，是公司提供的岗位/服务。){record_delimiter}
("entity"{tuple_delimiter}实习期{tuple_delimiter}TimeSpan{tuple_delimiter}李子茉在取得毕业证前所处的雇佣状态时间段。){record_delimiter}
("entity"{tuple_delimiter}毕业证{tuple_delimiter}Condition{tuple_delimiter}作为办理正式入职手续和结束实习期的前提条件。){record_delimiter}
("entity"{tuple_delimiter}劳动合同{tuple_delimiter}Contract{tuple_delimiter}待签订的正式合同，期限为三年。){record_delimiter}
("entity"{tuple_delimiter}三年{tuple_delimiter}TimeSpan{tuple_delimiter}劳动合同约定的合同期限长度。){record_delimiter}
("entity"{tuple_delimiter}试用期{tuple_delimiter}TimeSpan{tuple_delimiter}劳动合同开始后的六个月期间，是考核期。){record_delimiter}
("entity"{tuple_delimiter}六个月{tuple_delimiter}TimeSpan{tuple_delimiter}试用期所持续的具体时间段长度。){record_delimiter}
("entity"{tuple_delimiter}转正{tuple_delimiter}Condition{tuple_delimiter}试用期结束后，根据考核指标成绩确定的雇佣状态变化条件。){record_delimiter}
("entity"{tuple_delimiter}社会保险及公积金{tuple_delimiter}RightObligation{tuple_delimiter}公司在员工取得毕业证并办理入职后有义务缴纳的法定福利。){record_delimiter}
("entity"{tuple_delimiter}10日{tuple_delimiter}SpecificTime{tuple_delimiter}决定当月或次月缴纳社会保险及公积金的一个月度时间节点。){record_delimiter}
("entity"{tuple_delimiter}薪资{tuple_delimiter}RightObligation{tuple_delimiter}公司根据雇佣阶段（实习、试用、转正）支付给李子茉的报酬。){record_delimiter}
("entity"{tuple_delimiter}150元/天{tuple_delimiter}Amount{tuple_delimiter}实习期硕士研究生工资标准的具体金额及计算单位。){record_delimiter}
("entity"{tuple_delimiter}元{tuple_delimiter}Currency{tuple_delimiter}薪资标准所使用的货币单位。){record_delimiter}
("entity"{tuple_delimiter}天{tuple_delimiter}Unit{tuple_delimiter}实习期工资的度量单位。){record_delimiter}
("entity"{tuple_delimiter}120元/天{tuple_delimiter}Amount{tuple_delimiter}实习期本科工资标准的具体金额及计算单位。){record_delimiter}
("entity"{tuple_delimiter}9600元/月{tuple_delimiter}Amount{tuple_delimiter}试用期工资标准的具体金额及计算单位。){record_delimiter}
("entity"{tuple_delimiter}月{tuple_delimiter}Unit{tuple_delimiter}试用期及转正工资的度量单位。){record_delimiter}
("entity"{tuple_delimiter}12000元/月{tuple_delimiter}Amount{tuple_delimiter}转正后工资标准的具体金额及计算单位。){record_delimiter}
("entity"{tuple_delimiter}年终奖{tuple_delimiter}RightObligation{tuple_delimiter}根据公司及事业部经营情况确定的浮动奖金。){record_delimiter}
("entity"{tuple_delimiter}工作时间{tuple_delimiter}RightObligation{tuple_delimiter}公司规定的工作时间安排，包括两种可选时段和午休时间。){record_delimiter}
("entity"{tuple_delimiter}周一至周五{tuple_delimiter}DateTerm{tuple_delimiter}每周的工作日安排。){record_delimiter}
("entity"{tuple_delimiter}8:30-17:30 或 9:00-18:00{tuple_delimiter}TimeSpan{tuple_delimiter}每天可选择的具体工作时间段。){record_delimiter}
("entity"{tuple_delimiter}70分钟{tuple_delimiter}TimeSpan{tuple_delimiter}工作日午休的具体时长。){record_delimiter}
("entity"{tuple_delimiter}福利{tuple_delimiter}RightObligation{tuple_delimiter}公司根据不同雇佣阶段（实习、试用、转正）提供的补贴和待遇。){record_delimiter}
("entity"{tuple_delimiter}电脑补贴{tuple_delimiter}RightObligation{tuple_delimiter}实习期和试用期提供的每月100元补贴。){record_delimiter}
("entity"{tuple_delimiter}100元/月{tuple_delimiter}Amount{tuple_delimiter}电脑补贴的具体金额。){record_delimiter}
("entity"{tuple_delimiter}餐补{tuple_delimiter}RightObligation{tuple_delimiter}试用期开始提供的每月150元补贴。){record_delimiter}
("entity"{tuple_delimiter}150元/月{tuple_delimiter}Amount{tuple_delimiter}餐补的具体金额。){record_delimiter}
("entity"{tuple_delimiter}节假日福利{tuple_delimiter}RightObligation{tuple_delimiter}试用期开始享受的福利。){record_delimiter}
("entity"{tuple_delimiter}通讯补贴{tuple_delimiter}RightObligation{tuple_delimiter}转正后新增的福利之一。){record_delimiter}
("entity"{tuple_delimiter}带薪年假{tuple_delimiter}RightObligation{tuple_delimiter}转正后新增的福利之一。){record_delimiter}
("entity"{tuple_delimiter}薪酬保密制{tuple_delimiter}RightObligation{tuple_delimiter}公司要求员工必须遵守的一项制度，禁止泄露薪资信息。){record_delimiter}
("entity"{tuple_delimiter}解除劳动关系{tuple_delimiter}BreachClause{tuple_delimiter}违反薪酬保密制度等公司规定可能导致的法律后果。){record_delimiter}
("entity"{tuple_delimiter}笔记本电脑{tuple_delimiter}ProductService{tuple_delimiter}因工作需要，要求员工携带的个人物品。){record_delimiter}
("entity"{tuple_delimiter}无违法犯罪记录，无重大失信记录{tuple_delimiter}Condition{tuple_delimiter}签订正式劳动合同人员需满足的背景条件。){record_delimiter}
("entity"{tuple_delimiter}不予录用{tuple_delimiter}BreachClause{tuple_delimiter}若员工存在违法犯罪或重大失信记录，公司拥有的权利。){record_delimiter}
("entity"{tuple_delimiter}遵守公司的一切有关政策和规定{tuple_delimiter}RightObligation{tuple_delimiter}员工加入公司后需履行的基本义务。){record_delimiter}
("entity"{tuple_delimiter}不允许为其它公司做兼职工作或从事与本公司利益发生冲突的商业活动{tuple_delimiter}RightObligation{tuple_delimiter}员工需履行的竞业限制或忠诚义务。){record_delimiter}
("entity"{tuple_delimiter}居民身份证{tuple_delimiter}ProductService{tuple_delimiter}实习期报到需携带的个人身份证明文件。){record_delimiter}
("entity"{tuple_delimiter}中国招商银行卡{tuple_delimiter}ProductService{tuple_delimiter}实习期报到需携带的用于发放工资的银行账户证明。){record_delimiter}
("entity"{tuple_delimiter}学生证{tuple_delimiter}ProductService{tuple_delimiter}实习期报到需携带的学生身份证明文件。){record_delimiter}
("entity"{tuple_delimiter}A4纸{tuple_delimiter}Unit{tuple_delimiter}证件复印件所使用的纸张规格单位。){record_delimiter}
("entity"{tuple_delimiter}录用通知书{tuple_delimiter}Contract{tuple_delimiter}山东亿云信息技术有限公司向李子茉发出的法律文件，包含了录用意向和主要聘用条款。){record_delimiter}
("entity"{tuple_delimiter}公司{tuple_delimiter}Organization{tuple_delimiter}文中对山东亿云信息技术有限公司的简称。){record_delimiter}
("entity"{tuple_delimiter}亿云{tuple_delimiter}Organization{tuple_delimiter}文中对山东亿云信息技术有限公司的简称，指代公司平台和团队。){record_delimiter}
("entity"{tuple_delimiter}事业部{tuple_delimiter}Organization{tuple_delimiter}公司内部的组织单位，其经营情况影响年终奖的发放。){record_delimiter}
("entity"{tuple_delimiter}劳动关系{tuple_delimiter}Contract{tuple_delimiter}李子茉与山东亿云信息技术有限公司之间拟建立的雇佣法律关系。){record_delimiter}
("entity"{tuple_delimiter}解除劳动关系{tuple_delimiter}BreachClause{tuple_delimiter}违反薪酬保密制度等公司规定可能导致的法律后果，即合同终止。){record_delimiter}
("entity"{tuple_delimiter}正式劳动合同{tuple_delimiter}Contract{tuple_delimiter}待签订的具体合同文件，其签订需要满足携带特定材料和背景条件。){record_delimiter}
("entity"{tuple_delimiter}月{tuple_delimiter}Unit{tuple_delimiter}社会保险及公积金缴纳周期的度量单位，与10日这一节点相关。){record_delimiter}
("entity"{tuple_delimiter}当日{tuple_delimiter}SpecificTime{tuple_delimiter}指每月10日当天，是社保公积金缴纳操作的时间分界点。){record_delimiter}
("entity"{tuple_delimiter}次月{tuple_delimiter}DateTerm{tuple_delimiter}指每月10日之后的月份，是10日后办理入职时社保公积金的缴纳时间。){record_delimiter}
("entity"{tuple_delimiter}考核指标成绩{tuple_delimiter}Condition{tuple_delimiter}决定试用期员工是否能转正的评估标准和条件。){record_delimiter}
("entity"{tuple_delimiter}节假日{tuple_delimiter}DateTerm{tuple_delimiter}公司发放福利所依据的特定日期，如法定节日。){record_delimiter}
("entity"{tuple_delimiter}薪酬标准{tuple_delimiter}RightObligation{tuple_delimiter}公司支付给李子茉的不同阶段的薪资数额，属于需要保密的合同信息。){record_delimiter}
("relationship"{tuple_delimiter}山东亿云信息技术有限公司{tuple_delimiter}李子茉{tuple_delimiter}山东亿云信息技术有限公司是录用通知书的发出方和雇主，李子茉是接收方和潜在雇员，双方构成合同主体关系。){record_delimiter}
("relationship"{tuple_delimiter}山东亿云信息技术有限公司{tuple_delimiter}人工智能工程师{tuple_delimiter}山东亿云信息技术有限公司是提供人工智能工程师这一职位的组织。){record_delimiter}
("relationship"{tuple_delimiter}李子茉{tuple_delimiter}人工智能工程师{tuple_delimiter}李子茉被山东亿云信息技术有限公司邀请担任人工智能工程师这一职位。){record_delimiter}
("relationship"{tuple_delimiter}实习期{tuple_delimiter}毕业证{tuple_delimiter}实习期的结束以李子茉取得毕业证为条件。){record_delimiter}
("relationship"{tuple_delimiter}劳动合同{tuple_delimiter}三年{tuple_delimiter}劳动合同的期限是三年。){record_delimiter}
("relationship"{tuple_delimiter}劳动合同{tuple_delimiter}试用期{tuple_delimiter}劳动合同包含为期六个月的试用期条款。){record_delimiter}
("relationship"{tuple_delimiter}试用期{tuple_delimiter}六个月{tuple_delimiter}试用期的具体时长是六个月。){record_delimiter}
("relationship"{tuple_delimiter}试用期{tuple_delimiter}转正{tuple_delimiter}试用期结束后，满足条件可以转为正式员工。){record_delimiter}
("relationship"{tuple_delimiter}社会保险及公积金{tuple_delimiter}10日{tuple_delimiter}10日是一个关键日期节点，用于决定社保和公积金是当月还是次月缴纳。){record_delimiter}
("relationship"{tuple_delimiter}薪资{tuple_delimiter}150元/天{tuple_delimiter}150元/天是实习期硕士研究生薪资的具体标准。){record_delimiter}
("relationship"{tuple_delimiter}150元/天{tuple_delimiter}元{tuple_delimiter}150元/天中的货币单位是元。){record_delimiter}
("relationship"{tuple_delimiter}150元/天{tuple_delimiter}天{tuple_delimiter}150元/天中的薪酬计算单位是天。){record_delimiter}
("relationship"{tuple_delimiter}薪资{tuple_delimiter}120元/天{tuple_delimiter}120元/天是实习期本科薪资的具体标准。){record_delimiter}
("relationship"{tuple_delimiter}薪资{tuple_delimiter}9600元/月{tuple_delimiter}9600元/月是试用期薪资的具体标准。){record_delimiter}
("relationship"{tuple_delimiter}薪资{tuple_delimiter}12000元/月{tuple_delimiter}12000元/月是转正后薪资的具体标准。){record_delimiter}
("relationship"{tuple_delimiter}9600元/月{tuple_delimiter}月{tuple_delimiter}9600元/月中的薪酬计算单位是月。){record_delimiter}
("relationship"{tuple_delimiter}工作时间{tuple_delimiter}周一至周五{tuple_delimiter}工作时间为每周的周一至周五。){record_delimiter}
("relationship"{tuple_delimiter}工作时间{tuple_delimiter}8:30-17:30 或 9:00-18:00{tuple_delimiter}每天的具体工作时间段为8:30-17:30或9:00-18:00。){record_delimiter}
("relationship"{tuple_delimiter}工作时间{tuple_delimiter}70分钟{tuple_delimiter}工作时间内包含70分钟的午休时间。){record_delimiter}
("relationship"{tuple_delimiter}福利{tuple_delimiter}电脑补贴{tuple_delimiter}电脑补贴是福利的一部分。){record_delimiter}
("relationship"{tuple_delimiter}电脑补贴{tuple_delimiter}100元/月{tuple_delimiter}电脑补贴的金额是每月100元。){record_delimiter}
("relationship"{tuple_delimiter}福利{tuple_delimiter}餐补{tuple_delimiter}餐补是福利的一部分。){record_delimiter}
("relationship"{tuple_delimiter}餐补{tuple_delimiter}150元/月{tuple_delimiter}餐补的金额是每月150元。){record_delimiter}
("relationship"{tuple_delimiter}薪酬保密制{tuple_delimiter}解除劳动关系{tuple_delimiter}违反薪酬保密制将导致解除劳动关系的违约后果。){record_delimiter}
("relationship"{tuple_delimiter}无违法犯罪记录，无重大失信记录{tuple_delimiter}不予录用{tuple_delimiter}如果不能满足无违法犯罪和失信记录的条件，公司将行使不予录用的权利。){record_delimiter}
("relationship"{tuple_delimiter}居民身份证{tuple_delimiter}A4纸{tuple_delimiter}居民身份证复印件要求使用A4纸复印。){record_delimiter}
("relationship"{tuple_delimiter}中国招商银行卡{tuple_delimiter}A4纸{tuple_delimiter}中国招商银行卡复印件要求使用A4纸复印。){record_delimiter}
("relationship"{tuple_delimiter}学生证{tuple_delimiter}A4纸{tuple_delimiter}学生证复印件要求使用A4纸复印。){record_delimiter}
("relationship"{tuple_delimiter}录用通知书{tuple_delimiter}山东亿云信息技术有限公司{tuple_delimiter}录用通知书是由山东亿云信息技术有限公司发出的合同文件。){record_delimiter}
("relationship"{tuple_delimiter}录用通知书{tuple_delimiter}李子茉{tuple_delimiter}录用通知书是发送给李子茉的法律文件。){record_delimiter}
("relationship"{tuple_delimiter}公司{tuple_delimiter}山东亿云信息技术有限公司{tuple_delimiter}“公司”是“山东亿云信息技术有限公司”的简称，指向同一实体。){record_delimiter}
("relationship"{tuple_delimiter}亿云{tuple_delimiter}山东亿云信息技术有限公司{tuple_delimiter}“亿云”是“山东亿云信息技术有限公司”的简称或品牌称呼，指向同一实体。){record_delimiter}
("relationship"{tuple_delimiter}实习期{tuple_delimiter}社会保险及公积金{tuple_delimiter}在实习期（未毕业）期间，公司无法为李子茉缴纳社会保险及公积金。){record_delimiter}
("relationship"{tuple_delimiter}取得毕业证并办理入职手续{tuple_delimiter}社会保险及公积金{tuple_delimiter}在李子茉取得毕业证并办理入职手续后，公司开始为其缴纳社会保险及公积金。){record_delimiter}
("relationship"{tuple_delimiter}社会保险及公积金{tuple_delimiter}月{tuple_delimiter}社会保险及公积金的缴纳周期是按月计算的。){record_delimiter}
("relationship"{tuple_delimiter}10日{tuple_delimiter}当日{tuple_delimiter}文中的“10日前”指的是在“当日”（10日）这个时间点之前。){record_delimiter}
("relationship"{tuple_delimiter}10日{tuple_delimiter}次月{tuple_delimiter}文中的“10日后”指的是在10日之后办理入职，社保公积金将在“次月”缴纳。){record_delimiter}
("relationship"{tuple_delimiter}年终奖{tuple_delimiter}事业部{tuple_delimiter}年终奖的数额根据事业部（及公司）的经营情况确定。){record_delimiter}
("relationship"{tuple_delimiter}节假日福利{tuple_delimiter}节假日{tuple_delimiter}节假日福利是在“节假日”发放的福利待遇。){record_delimiter}
("relationship"{tuple_delimiter}试用期{tuple_delimiter}考核指标成绩{tuple_delimiter}试用期结束后是否转正，将根据“考核指标成绩”来确定。){record_delimiter}
("relationship"{tuple_delimiter}薪酬保密制{tuple_delimiter}薪酬标准{tuple_delimiter}薪酬保密制度要求员工对“薪酬标准”进行保密。){record_delimiter}
("relationship"{tuple_delimiter}薪酬标准{tuple_delimiter}150元/天{tuple_delimiter}150元/天是实习期硕士研究生的薪酬标准之一。){record_delimiter}
("relationship"{tuple_delimiter}薪酬标准{tuple_delimiter}120元/天{tuple_delimiter}120元/天是实习期本科生的薪酬标准之一。){record_delimiter}
("relationship"{tuple_delimiter}薪酬标准{tuple_delimiter}9600元/月{tuple_delimiter}9600元/月是试用期的薪酬标准。){record_delimiter}
("relationship"{tuple_delimiter}薪酬标准{tuple_delimiter}12000元/月{tuple_delimiter}12000元/月是转正后的薪酬标准。){record_delimiter}
("relationship"{tuple_delimiter}解除劳动关系{tuple_delimiter}劳动关系{tuple_delimiter}“解除劳动关系”是终止“劳动关系”这一法律关系的具体行动/条款。){completion_delimiter}
-真实数据-
实体类型：{entity_types}
文本：{input_text}
################
输出：
"""

CONTINUE_EN: str = """MANY entities and relationships were missed in the last extraction.  \
Add them below using the same format:
"""

CONTINUE_ZH: str = """很多实体和关系在上一次的提取中可能被遗漏了。请在下面使用相同的格式添加它们："""

IF_LOOP_EN: str = """It appears some entities and relationships may have still been missed.  \
Answer YES | NO if there are still entities and relationships that need to be added.
"""

IF_LOOP_ZH: str = """看起来可能仍然遗漏了一些实体和关系。如果仍有实体和关系需要添加，请回答YES | NO。"""

KG_EXTRACTION_PROMPT: dict = {
    "en": {
        "TEMPLATE": TEMPLATE_EN,
        "CONTINUE": CONTINUE_EN,
        "IF_LOOP": IF_LOOP_EN,
    },
    "zh": {
        "TEMPLATE": TEMPLATE_ZH,
        "CONTINUE": CONTINUE_ZH,
        "IF_LOOP": IF_LOOP_ZH,
    },
    "FORMAT": {
        "tuple_delimiter": "<|>",
        "record_delimiter": "##",
        "completion_delimiter": "<|COMPLETE|>"
    },
}