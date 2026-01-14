package com.cra.contract.service.impl;

import com.cra.contract.entity.ContractContent;
import com.cra.contract.entity.ContractMain;
import com.cra.contract.entity.ContractVersion;
import com.cra.contract.repository.ContractContentRepository;
import com.cra.contract.repository.ContractMainRepository;
import com.cra.contract.repository.ContractVersionRepository;
import com.cra.contract.service.ContractService;
import com.cra.common.exception.BusinessException;
import com.cra.common.model.Response;
import cn.dev33.satoken.stp.StpUtil;
import com.cra.contract.util.RemoteServerUtils;
import org.apache.tika.Tika;
import org.apache.tika.exception.TikaException;
import org.apache.tika.metadata.Metadata;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.DigestUtils;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.entity.mime.FileBody; // Added Import
import org.apache.hc.client5.http.entity.mime.MultipartEntityBuilder;
import org.apache.hc.client5.http.entity.mime.StringBody;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import com.cra.contract.websocket.ContractReviewWebSocket;
import org.apache.hc.client5.http.config.RequestConfig; // Added Import
import org.apache.hc.core5.util.Timeout; // Added Import

/**
 * 什么是事务?
 * 事务是一组必须要么全部成功、要么全部失败的数据库操作单元。它解决的问题是：如何保证数据一致性
 * 举个例子：假设有一个转账操作：A要扣100元的时候，B就能加100元
 * 对应同步执行的代码是：dao.decreaseA(100); --> dao.increaseB(100);
 * 没有事务的情况（危险） --> A 扣钱成功 -- > 此时程序异常 --> B 没加钱 --> 导致的结果就是数据不一致（钱“消失”了）
 * 有事务的情况（安全） --> 两步作为一个整体执行 任一步失败：全部回滚, 数据恢复到执行前状态
 * 事务的 4 个核心特性（ACID） --> Atomicity（原子性）要么全做，要么全不做 /  Consistency（一致性）数据始终合法 / Isolation（隔离性）多事务互不干扰 / Durability（持久性）提交后永久生效
 */
@Service
@Transactional // 类中所有 public 方法默认都开启事务
public class ContractServiceImpl implements ContractService {
    private static final Logger logger = LoggerFactory.getLogger(ContractServiceImpl.class);
    // TODO 写到配置文件里面
    private static final String STORAGE_DIR = "G:\\项目成果打包\\合同审查Agent\\test_cache";

    @Value("${ftp.host:}")
    private String ftpHost;

    @Value("${ftp.port:21}")
    private int ftpPort;

    @Value("${ftp.username:}")
    private String ftpUsername;

    @Value("${ftp.password:}")
    private String ftpPassword;

    @Value("${ftp.base-path:}")
    private String ftpBasePath;
    
    @Autowired // 用来告诉 Spring：这个对象我不自己 new，你帮我注入。 --> 等价于private ContractMainRepository contractMainRepository = new ContractMainRepository();
    private ContractMainRepository contractMainRepository;
    
    @Autowired
    private ContractVersionRepository contractVersionRepository;
    
    @Autowired
    private ContractContentRepository contractContentRepository;
    
    @Autowired
    private RemoteServerUtils remoteServerUtils;
    
    @Value("${remote.upload-path}")
    private String remoteUploadPath;
    
    @Value("${remote.ocr-output-path}")
    private String remoteOcrOutputPath;
    
    @Value("${remote.mineru-command:mineru}")
    private String mineruCommand;
    
    @Value("${python-service.base-url}")
    private String pythonServiceBaseUrl;

    private final Tika tika = new Tika();

    /**
     * 获取合同文件流展示给前端
     *
     * @param contractId
     * @param versionNumber
     * @return
     */
    @Override
    public InputStream getContractFile(Long contractId, Integer versionNumber) {
        try {
            ContractVersion version;
            if (versionNumber != null) {
                version = getContractVersion(contractId, versionNumber).getData();
            } else {
                version = getLatestContractVersion(contractId).getData();
            }
            String remotePath = version.getStoragePath();
            if (!org.springframework.util.StringUtils.hasText(remotePath)) {
                throw new BusinessException(404, "文件路径不存在");
            }
            // Create temp file
            File tempFile = File.createTempFile("contract_" + contractId + "_", ".pdf");
            // Download file
            remoteServerUtils.downloadFile(remotePath, tempFile);
            // Return stream
            return new java.io.FileInputStream(tempFile);
        } catch (Exception e) {
            logger.error("获取合同文件失败: {}", e.getMessage());
            throw new BusinessException(500, "获取合同文件失败");
        }
    }
    /**
     * 创建合同
     *
     * @param contract
     * @param file
     * @return
     */
    @Override
    public Response<ContractMain> createContract(ContractMain contract, MultipartFile file) {
        try {
            // 验证合同编号唯一性
            if (contractMainRepository.findByContractNumber(contract.getContractNumber()).isPresent()) {
                throw new BusinessException(400, "合同编号已存在");
            }
            
            // 设置合同状态的默认值 --> 刚上传的文件是草稿状态, 经过review阶段会变成待审核状态, 人工查看后会给出接受/拒绝状态
            if (contract.getStatus() == null) {
                contract.setStatus(0);
            }

            // 获取当前登录用户
             if (!StpUtil.isLogin()) {
                throw new BusinessException(401,"用户未登录，禁止执行上传合同的操作");
             }
             String creatorId = StpUtil.getLoginIdAsString();
//            // 开发模式
//            String creatorId = StpUtil.isLogin() ? StpUtil.getLoginIdAsString() : "system_auto"; // 条件 ? 表达式1 : 表达式2 如果条件为 true → 返回 表达式1 | 如果条件为 false → 返回 表达式2
//            if (!StpUtil.isLogin()) {
//                logger.warn("当前未登录，使用默认用户system_auto创建合同");
//            }
            contract.setCreatorId(creatorId);
            contract.setCreateTime(LocalDateTime.now());
            contract.setUpdateTime(LocalDateTime.now());
            // 保存合同基本信息
            ContractMain savedContract = contractMainRepository.save(contract);
            // 创建第一个版本
            // TODO 如果是空的话 应该提前校验 抛出异常 不然无法保证数据库的信息同步
            if (file != null && !file.isEmpty()) {
                createContractVersion(savedContract.getId(), file, "初始版本");
            }
            return Response.success("合同创建成功", savedContract);
        } catch (Exception e) {
            logger.error("创建合同失败: {}", e.getMessage(), e);
            throw new BusinessException(500, "创建合同失败: " + e.getMessage());
        }
    }

    /**
     * 更新合同
     *
     * @param contractId
     * @param contract
     * @return
     */
    @Override
    public Response<ContractMain> updateContract(Long contractId, ContractMain contract) {
        ContractMain existingContract = contractMainRepository.findById(contractId)
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));
        
        // 更新合同信息
        existingContract.setContractName(contract.getContractName());
        existingContract.setPartyAId(contract.getPartyAId());
        existingContract.setPartyBId(contract.getPartyBId());
        existingContract.setAmount(contract.getAmount());
        existingContract.setStartDate(contract.getStartDate());
        existingContract.setEndDate(contract.getEndDate());
        existingContract.setCategory(contract.getCategory());
        existingContract.setDepartment(contract.getDepartment());
        existingContract.setRemark(contract.getRemark());
        existingContract.setUpdateTime(LocalDateTime.now());
        
        return Response.success("合同更新成功", contractMainRepository.save(existingContract));
    }

    /**
     * 上传合同文件
     * @param file 上传的文件 只支持.pdf和.docx格式
     * @param category 合同类型
     * @param department 所属部门
     * @return
     */
    @Override
    public Response<ContractMain> uploadContractFile(MultipartFile file, String category, String department) {
        try {
            validateFileType(file);
            // 创建一个草稿合同
            ContractMain contract = new ContractMain();
            // 使用文件名作为合同名称 | 去除扩展名
            String fileName = file.getOriginalFilename();
            String contractName = fileName != null && fileName.contains(".") 
                    ? fileName.substring(0, fileName.lastIndexOf(".")) 
                    : fileName;
            
            contract.setContractName(contractName);
            // 生成临时合同编号
            contract.setContractNumber("DRAFT-" + System.currentTimeMillis() + "-" + new Random().nextInt(1000));
            contract.setStatus(0); // 上传的接口中 固定合同状态u为草稿
            
            // 设置类型和部门
            contract.setCategory(category);
            contract.setDepartment(department);

//            // 获取当前登录用户
//             if (!StpUtil.isLogin()) {
//                throw new BusinessException(401,"用户未登录，禁止执行上传合同的操作");
//             }
//             String creatorId = StpUtil.getLoginIdAsString();
//            // 开发模式
            String creatorId = StpUtil.isLogin() ? StpUtil.getLoginIdAsString() : "system_auto"; // 条件 ? 表达式1 : 表达式2 如果条件为 true → 返回 表达式1 | 如果条件为 false → 返回 表达式2
            if (!StpUtil.isLogin()) {
                logger.warn("当前未登录，使用默认用户system_auto创建合同");
            }

            contract.setCreatorId(creatorId);
            contract.setCreateTime(LocalDateTime.now());
            contract.setUpdateTime(LocalDateTime.now());
            // 设置默认值防止报错
            contract.setPartyAId(0L); // 占位
            contract.setPartyBId(0L); // 占位
            
            ContractMain savedContract = contractMainRepository.save(contract);
            createContractVersion(savedContract.getId(), file, "上传文件自动创建");
            logger.info("文件上传成功");
            return Response.success("文件上传成功，已创建合同草稿", savedContract);
        } catch (Exception e) {
            logger.error("上传文件失败: {}", e.getMessage(), e);
            throw new BusinessException(500, "上传文件失败: " + e.getMessage());
        }
    }
    /**
     * 批量上传合同文件
     * @param files 上传的批量文件 只支持.pdf和.docx格式
     * @param category 合同类型
     * @param department 所属部门
     * @return
     */
    @Override
    public Response<List<ContractMain>> batchUploadContractFiles(MultipartFile[] files, String category, String department) {
        List<ContractMain> createdContracts = new ArrayList<>();
        List<String> errors = new ArrayList<>();
        
        for (MultipartFile file : files) {
            try {
                if (file.isEmpty()) continue;
                Response<ContractMain> response = uploadContractFile(file, category, department);
                if (response.getData() != null) {
                    createdContracts.add(response.getData());
                }
            } catch (Exception e) {
                String fileName = file.getOriginalFilename();
                logger.error("批量上传中文件 {} 处理失败: {}", fileName, e.getMessage());
                errors.add("文件 " + fileName + " 失败: " + e.getMessage());
            }
        }
        
        if (createdContracts.isEmpty() && !errors.isEmpty()) {
            throw new BusinessException(500, "批量上传全部失败: " + String.join("; ", errors));
        }
        
        if (!errors.isEmpty()) {
            // 部分成功
            return Response.success("批量上传部分成功，失败详情: " + String.join("; ", errors), createdContracts);
        }
        
        return Response.success("批量上传成功", createdContracts);
    }

    /*
    删除合同
     */
    @Override
    public Response<String> deleteContract(Long contractId) {
        ContractMain contract = contractMainRepository.findById(contractId)
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));
        
        // 删除合同所有版本及物理文件
        List<ContractVersion> versions = contractVersionRepository.findByContractId(contractId);
        for (ContractVersion version : versions) {
            // 1. 删除数据库内容
            contractContentRepository.deleteByContractIdAndVersionId(contractId, version.getId());
            
            // 2. 尝试删除物理文件
            String storagePath = version.getStoragePath();
            if (StringUtils.hasText(storagePath)) {
                try {
                    deletePhysicalFile(storagePath);
                } catch (Exception e) {
                    // 仅记录日志，不阻断数据库删除流程
                    logger.error("删除物理文件失败: {} - {}", storagePath, e.getMessage());
                }
            }
            
            contractVersionRepository.delete(version);
        }
        
        // 删除合同
        contractMainRepository.delete(contract);
        
        return Response.success("合同删除成功");
    }

    /**
     * 删除物理文件（支持远程SFTP）
     */
    private void deletePhysicalFile(String storagePath) {
        // storagePath 现在是远程 Linux 路径
        try {
            remoteServerUtils.deleteFile(storagePath);
        } catch (Exception e) {
            logger.error("删除远程文件失败: {} - {}", storagePath, e.getMessage());
        }
    }


    /**
     * AI服务-审核合同
     */
    @Override
    public Response<ContractMain> reviewContract(ContractMain contract) {
        logger.info("开始AI服务-合同智能审核");
        // 校验合同
        ContractMain existingContract = contractMainRepository.findById(contract.getId())
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));

        // 推送开始消息
        ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "REVIEW_START", "PROCESSING", "开始合同智能审查");

        // 获取最新版本和合同ID
        ContractVersion latestVersion = getLatestContractVersion(existingContract.getId()).getData();
        String inputPath = latestVersion.getStoragePath();
        // 输出目录：/远程ocr目录/{contractId}/{version}/
        String outputDir = remoteOcrOutputPath + "/" + existingContract.getId() + "/" + latestVersion.getVersionNumber();
        try {
            /*
             * 合同审核第一步 --> OCR
             * */
            logger.info("step1-OCR服务");
            ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "OCR", "PROCESSING", "正在进行OCR识别...");

            String jsonResult = callMinerUApi(inputPath, outputDir);
            // 解析OCR-API的返回结果
            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode rootNode = objectMapper.readTree(jsonResult);
            JsonNode resultsNode = rootNode.path("results");
            // 结果结构: results -> {filename_without_ext: {md_content: "...", middle_json: {...}, ...}}
            if (resultsNode.isObject() && resultsNode.size() > 0) {
                String firstKey = resultsNode.fieldNames().next();
                JsonNode fileResultNode = resultsNode.get(firstKey);
                
                if (fileResultNode.has("md_content")) {
                    String mdContent = fileResultNode.get("md_content").asText();
                    // 更新合同到mongo数据库
                    ContractContent content = contractContentRepository.findByContractIdAndVersionId(
                            existingContract.getId(), latestVersion.getId())
                            .orElseThrow(() -> new BusinessException(404, "合同内容记录不存在"));
                    // 将 OCR 得到的 Markdown 更新进去
                    content.setContent(mdContent);
                    // 保存其他 JSON 字段
                    if (fileResultNode.has("middle_json")) {
                        content.setMiddleJson(fileResultNode.get("middle_json").toString());
                    }
                    if (fileResultNode.has("model_output")) {
                        content.setModelOutput(fileResultNode.get("model_output").toString());
                    }
                    if (fileResultNode.has("content_list")) {
                        content.setContentList(fileResultNode.get("content_list").toString());
                    }
                    // TODO ocr的图片怎么存?
                    contractContentRepository.save(content);
                    logger.info("OCR Markdown内容及详细数据已保存到MongoDB数据库");
                    // 准备推送给前端的数据
                    Map<String, Object> ocrData = new HashMap<>();
                    ocrData.put("md_content", mdContent);
                    // 更新进度: OCR完成
                    updateContractProgress(
                        existingContract.getId(), 
                        latestVersion.getId(), 
                        "OCR-Agent", 
                        "OCR完成",
                        null,
                        "OCR",
                        ocrData
                    );
                }
            }
            /*
             * 合同审核第2步 --> pycra
             * */
            logger.info("step2-pycra-CurrentContractKnowledgeGraphBuild服务");
            ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "KG_BUILD", "PROCESSING", "正在为当前合同构建知识图谱...");
            
            try {
                // 从数据库重新获取最新的 content
                ContractContent updatedContent = contractContentRepository.findByContractIdAndVersionId(
                        existingContract.getId(), latestVersion.getId())
                        .orElseThrow(() -> new BusinessException(404, "合同内容记录不存在"));
                
                String contractText = updatedContent.getContent();
                logger.info("合同文本长度: {}", contractText.length());
                if (StringUtils.hasText(contractText)) {
                    // TODO 分别提取出来各个字段
                    String kgResult = callKnowledgeGraphBuildApi(contractText, String.valueOf(existingContract.getId()));
                    logger.info("知识图谱构建成功");
                    // 保存图谱数据
                    updatedContent.setKnowledgeGraph(kgResult);
                    contractContentRepository.save(updatedContent);
                    logger.info("知识图谱数据已保存到MongoDB");
                    // 解析图谱数据用于推送
                    JsonNode kgJson = objectMapper.readTree(kgResult);
                    // 更新进度: KG完成
                    updateContractProgress(
                        existingContract.getId(), 
                        latestVersion.getId(), 
                        "pycra-CCKG-Agent", 
                        "pycra-cckg完成",
                        null,
                        "KG_BUILD",
                        kgJson
                    );
                } else {
                    logger.warn("合同内容为空，跳过知识图谱构建");
                    ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "KG_BUILD", "SKIPPED", "合同内容为空");
                }
            } catch (Exception e) {
                logger.error("知识图谱构建服务调用失败，但不影响OCR结果: {}", e.getMessage(), e);
                // 不抛出异常，保证OCR结果能返回给用户
                ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "KG_BUILD", "FAILED", e.getMessage());
            }

            ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "REVIEW_ALL", "COMPLETED", "合同审查全流程结束");
            return Response.success("合同审查已完成，请前端发送一个提示给用户", existingContract);
            
        } catch (Exception e) {
            logger.error("合同审查失败: {}", e.getMessage(), e);
            ContractReviewWebSocket.sendMessage(String.valueOf(contract.getId()), "REVIEW_ALL", "FAILED", e.getMessage());
            throw new BusinessException(500, "合同审查失败: " + e.getMessage());
        }
    }

    /**
     * 更新合同进度并推送WebSocket消息
     * @param contractId 合同ID
     * @param versionId 版本ID
     * @param agentName 当前处理Agent名称
     * @param remark 进度备注
     * @param versionNumber (可选) 更新版本号
     * @param stepName (可选) 步骤名称，用于WebSocket推送
     * @param stepData (可选) 步骤数据，用于WebSocket推送
     */
    private void updateContractProgress(Long contractId, Long versionId, String agentName, String remark, Integer versionNumber, String stepName, Object stepData) {
        try {
            // 1. 数据库更新
            ContractMain contract = contractMainRepository.findById(contractId)
                    .orElseThrow(() -> new BusinessException(404, "合同不存在"));
            contract.setSetorId(agentName);
            contract.setUpdateTime(LocalDateTime.now());
            contractMainRepository.save(contract);
            logger.info("{}: 更新合同Main数据库 - {}", agentName, remark);

            ContractVersion version = contractVersionRepository.findById(versionId)
                    .orElseThrow(() -> new BusinessException(404, "合同版本不存在"));
            version.setRemark(remark);
            if (versionNumber != null) {
                version.setVersionNumber(versionNumber);
            }
            contractVersionRepository.save(version);
            logger.info("{}: 更新合同Version数据库 - {}", agentName, remark);
            
            // 2. WebSocket 推送
            if (StringUtils.hasText(stepName)) {
                ContractReviewWebSocket.sendMessage(
                    String.valueOf(contractId), 
                    stepName, 
                    "COMPLETED", 
                    stepData != null ? stepData : remark
                );
            }
            
        } catch (Exception e) {
            logger.error("更新合同进度失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 调用 Python 服务构建知识图谱
     * @param contractText 合同文本
     * @param contractId 合同ID
     * @return 响应JSON字符串
     */
    private String callKnowledgeGraphBuildApi(String contractText, String contractId) throws IOException {
        String apiUrl = pythonServiceBaseUrl + "/cckg/build";
        
        // 设置 5 分钟超时
        org.apache.hc.client5.http.config.RequestConfig requestConfig = org.apache.hc.client5.http.config.RequestConfig.custom()
                .setResponseTimeout(org.apache.hc.core5.util.Timeout.ofMinutes(5))
                .setConnectionRequestTimeout(org.apache.hc.core5.util.Timeout.ofSeconds(30))
                .build();
        
        try (CloseableHttpClient httpClient = HttpClients.custom()
                .setDefaultRequestConfig(requestConfig)
                .build()) {
            HttpPost httpPost = new HttpPost(apiUrl);
            httpPost.setHeader("Content-Type", "application/json");
            // build body
            Map<String, String> params = new HashMap<>();
            params.put("contract_text", contractText);
            params.put("contract_id", contractId);
            ObjectMapper objectMapper = new ObjectMapper();
            String jsonBody = objectMapper.writeValueAsString(params);
            httpPost.setEntity(new org.apache.hc.core5.http.io.entity.StringEntity(jsonBody, ContentType.APPLICATION_JSON));
            try (CloseableHttpResponse response = httpClient.execute(httpPost)) {
                int statusCode = response.getCode();
                HttpEntity responseEntity = response.getEntity();
                
                String result = "";
                try {
                    result = responseEntity != null ? EntityUtils.toString(responseEntity, StandardCharsets.UTF_8) : "";
                } catch (org.apache.hc.core5.http.ParseException e) {
                    logger.error("解析响应失败", e);
                    throw new IOException("解析响应失败", e);
                }
                
                if (statusCode == 200) {
                    return result;
                } else {
                    logger.error("知识图谱API调用失败: code={}, response={}", statusCode, result);
                    throw new IOException("知识图谱API调用失败: " + statusCode + ", " + result);
                }
            }
        }
    }

    /**
     * 调用 MinerU HTTP API
     * @param remoteFilePath Linux服务器上的文件绝对路径
     * @param outputDir Linux服务器上的输出目录绝对路径
     * @return 响应JSON字符串
     */
    private String callMinerUApi(String remoteFilePath, String outputDir) throws IOException {
        // TODO 写到配置文件
        String apiUrl = "http://your_ap:30000/file_parse"; // OCR服务地址
        
        try (CloseableHttpClient httpClient = HttpClients.createDefault()) {
            // 下载远程文件到本地临时文件
            File tempFile = File.createTempFile("ocr_upload_", ".pdf");
            try {
                // 使用 SFTP 下载
                remoteServerUtils.downloadFile(remoteFilePath, tempFile);
                // 构造 HTTP 请求
                HttpPost httpPost = new HttpPost(apiUrl);
                // 构建 Multipart 请求体
                MultipartEntityBuilder builder = MultipartEntityBuilder.create();
                // 添加文件参数 "files" (对应 FastAPI 的 UploadFile)
                builder.addPart("files", new FileBody(tempFile, ContentType.DEFAULT_BINARY));
                // 添加其他参数
                builder.addPart("output_dir", new StringBody(outputDir, ContentType.TEXT_PLAIN));
                builder.addPart("backend", new StringBody("hybrid-auto-engine", ContentType.TEXT_PLAIN)); // 用户反馈返回的是 hybrid-auto-engine
                // 添加返回参数
                builder.addPart("return_middle_json", new StringBody("true", ContentType.TEXT_PLAIN));
                builder.addPart("return_model_output", new StringBody("true", ContentType.TEXT_PLAIN));
                builder.addPart("return_content_list", new StringBody("true", ContentType.TEXT_PLAIN));
                builder.addPart("formula_enable", new StringBody("true", ContentType.TEXT_PLAIN));
                builder.addPart("table_enable", new StringBody("true", ContentType.TEXT_PLAIN));
                builder.addPart("return_images", new StringBody("true", ContentType.TEXT_PLAIN));
                HttpEntity multipart = builder.build();
                httpPost.setEntity(multipart);
                 
                logger.info("向OCR服务发送请求: {}", apiUrl);
                 
                try (CloseableHttpResponse response = httpClient.execute(httpPost)) {
                     int statusCode = response.getCode();
                     HttpEntity responseEntity = response.getEntity();
                     String result = responseEntity != null ? EntityUtils.toString(responseEntity) : "";
                     
                     if (statusCode == 200) {
                         return result;
                     } else {
                         logger.error("OCR API调用失败: code={}, response={}", statusCode, result);
                         throw new IOException("OCR API调用失败: " + statusCode);
                     }
                }
                 
                 /*
                  * 备用方案：如果 MinerU 服务与 Java 服务部署在同一台机器（或通过 SSH 操作），
                  * 可以使用 curl 命令直接在服务器本地发起请求，避免文件下载上传的流量。
                  * 
                  * String curlCommand = String.format(
                  *     "curl -X POST \"http://127.0.0.1:30000/file_parse\" " +
                  *     "-H \"accept: application/json\" " +
                  *     "-H \"Content-Type: multipart/form-data\" " +
                  *     "-F \"files=@%s\" " +
                  *     "-F \"output_dir=%s\" " +
                  *     "-F \"backend=hybrid-auto-engine\"",
                  *     remoteFilePath, outputDir
                  * );
                  * return remoteServerUtils.executeCommand(curlCommand);
                  */
                  
             } finally {
                 if (tempFile.exists()) tempFile.delete();
             }
        } catch (Exception e) {
            throw new IOException("调用OCR API失败", e);
        }
    }
    
    // 辅助方法
    private String extractPlainText(byte[] fileBytes, String fileName)
            throws IOException, TikaException {

        Metadata metadata = new Metadata();
        metadata.set("resourceName", fileName);

        try (InputStream is = new ByteArrayInputStream(fileBytes)) {
            return tika.parseToString(is, metadata);
        }
    }
    
    private String convertToHtml(String plainText) {
        // 简单转换，实际应该使用更复杂的HTML生成逻辑
        return plainText.replaceAll("\\n", "<br>")
                        .replaceAll("\\t", "&nbsp;&nbsp;&nbsp;&nbsp;");
    }

    /**
     * 验证文件类型 只支持/pdf和.docx文件
     * @param file
     */
    private void validateFileType(MultipartFile file) {
        String fileName = file.getOriginalFilename();
        if (fileName == null || (!fileName.toLowerCase().endsWith(".pdf") && !fileName.toLowerCase().endsWith(".docx"))) {
            throw new BusinessException(400, "不支持的文件类型，仅支持 .pdf 和 .docx");
        }
    }

    /**
     * 保存文件到远程服务器
     */
    private String saveFileToRemote(MultipartFile file) throws IOException {
        String originalFileName = file.getOriginalFilename();
        // 生成唯一文件名: UUID + 原始文件名
        String uniqueFileName = UUID.randomUUID().toString() + "_" + originalFileName;
        
        try {
            return remoteServerUtils.uploadFile(file.getInputStream(), remoteUploadPath, uniqueFileName);
        } catch (Exception e) {
            logger.error("文件上传远程服务器失败: {}", e.getMessage(), e);
            throw new IOException("文件上传失败: " + e.getMessage());
        }
    }

    @Override
    public Response<ContractMain> getContractById(Long contractId) {
        ContractMain contract = contractMainRepository.findById(contractId)
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));
        return Response.success(contract);
    }
    
    @Override
    public Response<ContractMain> getContractByNumber(String contractNumber) {
        ContractMain contract = contractMainRepository.findByContractNumber(contractNumber)
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));
        return Response.success(contract);
    }
    
    @Override
    public Response<Page<ContractMain>> getAllContracts(Pageable pageable) {
        return Response.success(contractMainRepository.findAll(pageable));
    }
    
    @Override
    public Response<Page<ContractMain>> searchContracts(String keyword, Pageable pageable) {
        return Response.success(contractMainRepository.findByContractNameContainingOrContractNumberContaining(
                keyword, keyword, pageable));
    }
    
    @Override
    public Response<List<ContractMain>> getContractsByStatus(Integer status) {
        return Response.success(contractMainRepository.findByStatus(status));
    }
    
    @Override
    public Response<List<ContractMain>> getContractsByCreator(String creatorId) {
        return Response.success(contractMainRepository.findByCreatorId(creatorId));
    }
    
    @Override
    public Response<List<ContractMain>> getContractsByParty(Long partyId) {
        return Response.success(contractMainRepository.findByPartyAIdOrPartyBId(partyId, partyId));
    }
    
    @Override
    public Response<List<ContractMain>> getContractsByCategory(String category) {
        return Response.success(contractMainRepository.findByCategory(category));
    }
    
    @Override
    public Response<List<ContractMain>> getContractsByDepartment(String department) {
        return Response.success(contractMainRepository.findByDepartment(department));
    }
    
    @Override
    public Response<ContractVersion> createContractVersion(Long contractId, MultipartFile file, String remark) {
        try {
            validateFileType(file);
            contractMainRepository.findById(contractId)
                    .orElseThrow(() -> new BusinessException(404, "合同不存在"));
            // 读取文件内容用于哈希和文本提取
            byte[] fileBytes = file.getBytes();
            String contentHash = DigestUtils.md5DigestAsHex(fileBytes);
            // 检查是否与现有版本内容重复
            if (contractVersionRepository.findByContentHash(contentHash).isPresent()) {
                throw new BusinessException(400, "文件内容与现有版本重复");
            }
            // 保存文件到远程服务器
            String storagePath = saveFileToRemote(file);
            
            // 提取纯文本
            String plainText = extractPlainText(fileBytes, file.getOriginalFilename());
            
            // 计算新版本号
            Integer newVersionNumber = contractVersionRepository.countByContractId(contractId) + 1;
            
            // 创建版本记录
            ContractVersion version = new ContractVersion();
            version.setContractId(contractId);
            version.setVersionNumber(newVersionNumber);
            version.setContentHash(contentHash);
            version.setStoragePath(storagePath); // 设置远程存储路径
            version.setFileName(file.getOriginalFilename());
            version.setFileType(file.getContentType());
            version.setFileSize(file.getSize());
            
            // 获取当前登录用户，如果未登录则使用默认系统用户
            // TODO 生产环境需从登录用户获取
            String creatorId = StpUtil.isLogin() ? StpUtil.getLoginIdAsString() : "system_auto";
            version.setCreatorId(creatorId);
            
            version.setRemark(remark);
            version.setCreateTime(LocalDateTime.now());
            
            ContractVersion savedVersion = contractVersionRepository.save(version);
            
            // 保存合同内容 (MongoDB)
            ContractContent contractContent = new ContractContent();
            contractContent.setContractId(contractId);
            contractContent.setVersionId(savedVersion.getId());
            // contractContent.setContent(content); // 不再存储原始文件内容到MongoDB
            contractContent.setPlainTextContent(plainText);
            contractContent.setHtmlContent(convertToHtml(plainText));
            contractContent.setCreatorId(creatorId);
            contractContent.setCreateTime(LocalDateTime.now());
            contractContent.setUpdateTime(LocalDateTime.now());
            
            contractContentRepository.save(contractContent);
            
            return Response.success("版本创建成功", savedVersion);
        } catch (IOException | TikaException e) {
            logger.error("创建合同版本失败: {}", e.getMessage(), e);
            throw new BusinessException(500, "创建合同版本失败: " + e.getMessage());
        }
    }
    
    @Override
    public Response<ContractVersion> getContractVersion(Long contractId, Integer versionNumber) {
        ContractVersion version = contractVersionRepository.findByContractIdAndVersionNumber(contractId, versionNumber)
                .orElseThrow(() -> new BusinessException(404, "版本不存在"));
        return Response.success(version);
    }
    
    @Override
    public Response<List<ContractVersion>> getContractVersions(Long contractId) {
        return Response.success(contractVersionRepository.findByContractId(contractId));
    }
    
    @Override
    public Response<ContractVersion> getLatestContractVersion(Long contractId) {
        ContractVersion version = contractVersionRepository.findTopByContractIdOrderByVersionNumberDesc(contractId)
                .orElseThrow(() -> new BusinessException(404, "合同无版本记录"));
        return Response.success(version);
    }
    
    @Override
    public Response<Map<String, Object>> compareContractVersions(Long contractId, Integer version1, Integer version2) {
        // 简化实现，实际应该使用专业的文本对比库
        ContractVersion v1 = getContractVersion(contractId, version1).getData();
        ContractVersion v2 = getContractVersion(contractId, version2).getData();
        
        ContractContent content1 = contractContentRepository.findByContractIdAndVersionId(contractId, v1.getId())
                .orElseThrow(() -> new BusinessException(404, "版本内容不存在"));
        ContractContent content2 = contractContentRepository.findByContractIdAndVersionId(contractId, v2.getId())
                .orElseThrow(() -> new BusinessException(404, "版本内容不存在"));
        
        Map<String, Object> result = new HashMap<>();
        result.put("version1", v1);
        result.put("version2", v2);
        result.put("content1", content1.getPlainTextContent());
        result.put("content2", content2.getPlainTextContent());
        result.put("diff", "版本对比功能待实现");
        
        return Response.success(result);
    }
    
    @Override
    public Response<ContractContent> getContractContent(Long contractId, Integer versionNumber) {
        ContractVersion version = versionNumber != null 
                ? getContractVersion(contractId, versionNumber).getData()
                : getLatestContractVersion(contractId).getData();
        
        ContractContent content = contractContentRepository.findByContractIdAndVersionId(contractId, version.getId())
                
                .orElseThrow(() -> new BusinessException(404, "合同内容不存在"));
        
        return Response.success(content);
    }
    
    @Override
    public Response<String> getContractPlainText(Long contractId, Integer versionNumber) {
        ContractVersion version = versionNumber != null 
                ? getContractVersion(contractId, versionNumber).getData()
                : getLatestContractVersion(contractId).getData();
        
        String content = contractContentRepository.findByContractIdAndVersionId(contractId, version.getId())
                .map(ContractContent::getPlainTextContent)
                .orElseThrow(() -> new BusinessException(404, "合同内容不存在"));
        
        return Response.success(content);
    }
    
    @Override
    public Response<String> getContractHtmlContent(Long contractId, Integer versionNumber) {
        ContractVersion version = versionNumber != null 
                ? getContractVersion(contractId, versionNumber).getData()
                : getLatestContractVersion(contractId).getData();
        
        String content = contractContentRepository.findByContractIdAndVersionId(contractId, version.getId())
                .map(ContractContent::getHtmlContent)
                .orElseThrow(() -> new BusinessException(404, "合同内容不存在"));
        
        return Response.success(content);
    }
    
    @Override
    public Response<ContractMain> updateContractStatus(Long contractId, Integer status) {
        ContractMain contract = contractMainRepository.findById(contractId)
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));
        
        contract.setStatus(status);
        contract.setUpdateTime(LocalDateTime.now());
        
        return Response.success("合同状态更新成功", contractMainRepository.save(contract));
    }
    
    @Override
    public Response<byte[]> exportContract(Long contractId, Integer versionNumber, String format) {
        try {
            ContractVersion version = versionNumber != null 
                    ? getContractVersion(contractId, versionNumber).getData()
                    : getLatestContractVersion(contractId).getData();
            
            ContractContent content = contractContentRepository.findByContractIdAndVersionId(contractId, version.getId())
                    .orElseThrow(() -> new BusinessException(404, "合同内容不存在"));
            
            byte[] exportContent;
            switch (format.toLowerCase()) {
                case "txt":
                    exportContent = content.getPlainTextContent().getBytes(StandardCharsets.UTF_8);
                    break;
                case "html":
                    exportContent = content.getHtmlContent().getBytes(StandardCharsets.UTF_8);
                    break;
                default:
                    exportContent = content.getContent().getBytes(StandardCharsets.UTF_8);
            }
            
            return Response.success("合同导出成功", exportContent);
        } catch (Exception e) {
            logger.error("导出合同失败: {}", e.getMessage(), e);
            throw new BusinessException(500, "导出合同失败: " + e.getMessage());
        }
    }
    
    @Override
    public Response<List<Map<String, Object>>> searchContractContent(Long contractId, String keyword) {
        ContractVersion latestVersion = getLatestContractVersion(contractId).getData();
        
        ContractContent content = contractContentRepository.findByContractIdAndVersionId(contractId, latestVersion.getId())
                .orElseThrow(() -> new BusinessException(404, "合同内容不存在"));
        
        List<Map<String, Object>> results = new ArrayList<>();
        String plainText = content.getPlainTextContent();
        String lowerCasePlainText = plainText.toLowerCase();
        String lowerCaseKeyword = keyword.toLowerCase();
        
        int index = lowerCasePlainText.indexOf(lowerCaseKeyword);
        while (index != -1) {
            Map<String, Object> result = new HashMap<>();
            result.put("keyword", keyword);
            result.put("position", index);
            
            // 获取更丰富的前后文
            int start = Math.max(0, index - 100);
            int end = Math.min(plainText.length(), index + keyword.length() + 100);
            
            // 高亮匹配的关键词
            String context = plainText.substring(start, end);
            String highlightedContext = context.replaceAll(
                "(?i)" + keyword, 
                "<mark>$0</mark>"
            );
            
            result.put("context", highlightedContext);
            result.put("version", latestVersion.getVersionNumber());
            results.add(result);
            
            index = lowerCasePlainText.indexOf(lowerCaseKeyword, index + 1);
        }
        
        return Response.success("内容搜索完成", results);
    }
    
    @Override
    public Response<List<Map<String, Object>>> searchAllContractContent(String keyword) {
        // TODO 实际项目中应使用Elasticsearch进行全文搜索
        List<Map<String, Object>> results = new ArrayList<>();
        
        // 获取所有合同
        List<ContractMain> contracts = contractMainRepository.findAll();
        
        for (ContractMain contract : contracts) {
            try {
                // 获取最新版本内容
                ContractVersion latestVersion = getLatestContractVersion(contract.getId()).getData();
                ContractContent content = contractContentRepository.findByContractIdAndVersionId(contract.getId(), latestVersion.getId())
                        .orElse(null);
                
                if (content != null) {
                    String plainText = content.getPlainTextContent();
                    if (plainText.contains(keyword)) {
                        Map<String, Object> result = new HashMap<>();
                        result.put("contractId", contract.getId());
                        result.put("contractName", contract.getContractName());
                        result.put("contractNumber", contract.getContractNumber());
                        
                        // 获取第一个匹配的上下文
                        int index = plainText.indexOf(keyword);
                        if (index != -1) {
                            int start = Math.max(0, index - 50);
                            int end = Math.min(plainText.length(), index + keyword.length() + 50);
                            result.put("context", plainText.substring(start, end));
                        }
                        
                        results.add(result);
                    }
                }
            } catch (Exception e) {
                logger.error("搜索合同 {} 内容失败: {}", contract.getId(), e.getMessage(), e);
                // 继续搜索其他合同
            }
        }
        
        return Response.success("全局内容搜索完成", results);
    }
}
