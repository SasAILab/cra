package com.cra.contract.entity;

import lombok.Data;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDateTime;

// mongodb
@Document(collection = "contract_content")
@Data
public class ContractContent {
    private String id;
    
    private Long contractId; // 关联合同ID
    
    private Long versionId; // 关联版本ID
    
    private String content; // 合同全文内容
    
    private String plainTextContent; // 纯文本内容（用于搜索）
    
    private String htmlContent; // HTML格式内容（用于展示）
    
    private String extractedClauses; // 提取的条款（JSON格式）
    
    private String metadata; // 文档元数据（JSON格式）
    
    // OCR 详细结果字段
    private String middleJson; // 中间处理结果 (middle.json)
    private String modelOutput; // 模型推理结果 (model.json)
    private String contentList; // 内容列表 (content_list.json)

    private String knowledgeGraph; // 知识图谱数据 (Nodes + Edges)
    
    private String creatorId; // 创建人ID
    
    private LocalDateTime createTime; // 创建时间
    
    private LocalDateTime updateTime; // 更新时间

}
