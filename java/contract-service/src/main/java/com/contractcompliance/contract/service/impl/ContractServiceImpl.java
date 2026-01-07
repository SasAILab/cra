package com.contractcompliance.contract.service.impl;

import com.contractcompliance.contract.entity.ContractContent;
import com.contractcompliance.contract.entity.ContractMain;
import com.contractcompliance.contract.entity.ContractVersion;
import com.contractcompliance.contract.repository.ContractContentRepository;
import com.contractcompliance.contract.repository.ContractMainRepository;
import com.contractcompliance.contract.repository.ContractVersionRepository;
import com.contractcompliance.contract.service.ContractService;
import com.contractcompliance.common.exception.BusinessException;
import com.contractcompliance.common.model.Response;
import cn.dev33.satoken.stp.StpUtil;
import org.apache.tika.Tika;
import org.apache.tika.exception.TikaException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.DigestUtils;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Transactional
public class ContractServiceImpl implements ContractService {
    
    private static final Logger logger = LoggerFactory.getLogger(ContractServiceImpl.class);
    
    @Autowired
    private ContractMainRepository contractMainRepository;
    
    @Autowired
    private ContractVersionRepository contractVersionRepository;
    
    @Autowired
    private ContractContentRepository contractContentRepository;
    
    private final Tika tika = new Tika();
    
    @Override
    public Response<ContractMain> createContract(ContractMain contract, MultipartFile file) {
        try {
            // 验证合同编号唯一性
            if (contractMainRepository.findByContractNumber(contract.getContractNumber()).isPresent()) {
                throw new BusinessException(400, "合同编号已存在");
            }
            
            // 设置默认值
            if (contract.getStatus() == null) {
                contract.setStatus(0); // 草稿状态
            }
            contract.setCreatorId(StpUtil.getLoginIdAsString()); // 从认证信息获取
            contract.setCreateTime(LocalDateTime.now());
            contract.setUpdateTime(LocalDateTime.now());
            
            // 保存合同基本信息
            ContractMain savedContract = contractMainRepository.save(contract);
            
            // 创建第一个版本
            if (file != null && !file.isEmpty()) {
                createContractVersion(savedContract.getId(), file, "初始版本");
            }
            
            return Response.success(savedContract, "合同创建成功");
        } catch (Exception e) {
            logger.error("创建合同失败: {}", e.getMessage(), e);
            throw new BusinessException(500, "创建合同失败: " + e.getMessage());
        }
    }
    
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
        
        return Response.success(contractMainRepository.save(existingContract), "合同更新成功");
    }
    
    @Override
    public Response<String> deleteContract(Long contractId) {
        ContractMain contract = contractMainRepository.findById(contractId)
                .orElseThrow(() -> new BusinessException(404, "合同不存在"));
        
        // 删除合同所有版本
        List<ContractVersion> versions = contractVersionRepository.findByContractId(contractId);
        for (ContractVersion version : versions) {
            contractContentRepository.deleteByContractIdAndVersionId(contractId, version.getId());
            contractVersionRepository.delete(version);
        }
        
        // 删除合同
        contractMainRepository.delete(contract);
        
        return Response.success("合同删除成功");
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
            // 验证合同存在
            contractMainRepository.findById(contractId)
                    .orElseThrow(() -> new BusinessException(404, "合同不存在"));
            
            // 读取文件内容
            byte[] fileBytes = file.getBytes();
            String content = new String(fileBytes, StandardCharsets.UTF_8);
            String plainText = extractPlainText(fileBytes, file.getOriginalFilename());
            String contentHash = DigestUtils.md5DigestAsHex(fileBytes);
            
            // 检查是否与现有版本内容重复
            if (contractVersionRepository.findByContentHash(contentHash).isPresent()) {
                throw new BusinessException(400, "文件内容与现有版本重复");
            }
            
            // 计算新版本号
            Integer newVersionNumber = contractVersionRepository.countByContractId(contractId) + 1;
            
            // 创建版本记录
            ContractVersion version = new ContractVersion();
            version.setContractId(contractId);
            version.setVersionNumber(newVersionNumber);
            version.setContentHash(contentHash);
            version.setFileName(file.getOriginalFilename());
            version.setFileType(file.getContentType());
            version.setFileSize(file.getSize());
            version.setCreatorId(StpUtil.getLoginIdAsString()); // 从认证信息获取
            version.setRemark(remark);
            version.setCreateTime(LocalDateTime.now());
            
            ContractVersion savedVersion = contractVersionRepository.save(version);
            
            // 保存合同内容
            ContractContent contractContent = new ContractContent();
            contractContent.setContractId(contractId);
            contractContent.setVersionId(savedVersion.getId());
            contractContent.setContent(content);
            contractContent.setPlainTextContent(plainText);
            contractContent.setHtmlContent(convertToHtml(plainText));
            contractContent.setCreatorId(StpUtil.getLoginIdAsString()); // 从认证信息获取
            contractContent.setCreateTime(LocalDateTime.now());
            contractContent.setUpdateTime(LocalDateTime.now());
            
            contractContentRepository.save(contractContent);
            
            return Response.success(savedVersion, "版本创建成功");
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
    public Response<String> getContractContent(Long contractId, Integer versionNumber) {
        ContractVersion version = versionNumber != null 
                ? getContractVersion(contractId, versionNumber).getData()
                : getLatestContractVersion(contractId).getData();
        
        String content = contractContentRepository.findByContractIdAndVersionId(contractId, version.getId())
                .map(ContractContent::getContent)
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
        
        return Response.success(contractMainRepository.save(contract), "合同状态更新成功");
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
            
            return Response.success(exportContent, "合同导出成功");
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
        
        return Response.success(results, "内容搜索完成");
    }
    
    @Override
    public Response<List<Map<String, Object>>> searchAllContractContent(String keyword) {
        // 简单实现，实际项目中应使用Elasticsearch进行全文搜索
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
        
        return Response.success(results, "全局内容搜索完成");
    }
    
    // 辅助方法
    private String extractPlainText(byte[] fileBytes, String fileName) throws IOException, TikaException {
        // 使用Tika提取纯文本
        return tika.parseToString(fileBytes);
    }
    
    private String convertToHtml(String plainText) {
        // 简单转换，实际应该使用更复杂的HTML生成逻辑
        return plainText.replaceAll("\\n", "<br>")
                        .replaceAll("\\t", "&nbsp;&nbsp;&nbsp;&nbsp;");
    }
}
