package com.cra.contract.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

/**
 * 临时修复数据库表结构
 * 在项目启动时执行，修复完成后可删除
 */
@Component
public class DatabaseFixer implements CommandLineRunner {

    private static final Logger logger = LoggerFactory.getLogger(DatabaseFixer.class);

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(String... args) throws Exception {
        logger.info("DatabaseFixer: 开始检查数据库表结构...");
        
        try {
            // 尝试添加 setor_id 字段
            // 注意：如果字段已存在，PostgreSQL 会报错，所以我们捕获异常
            // 修正：由于表中有历史数据，添加 NOT NULL 列必须指定默认值
            String sql = "ALTER TABLE contract_main ADD COLUMN setor_id VARCHAR(255) DEFAULT 'system' NOT NULL";
            jdbcTemplate.execute(sql);
            logger.info("DatabaseFixer: 成功添加字段 setor_id (默认值: system)");
        } catch (Exception e) {
            // 如果是因为字段已存在，则忽略
            if (e.getMessage().contains("already exists") || e.getMessage().contains("已存在")) {
                logger.info("DatabaseFixer: 字段 setor_id 已存在，无需添加");
            } else {
                logger.warn("DatabaseFixer: 添加字段 setor_id 失败 (可能是因为已存在或其他原因): {}", e.getMessage());
            }
        }
        
        logger.info("DatabaseFixer: 数据库检查完成");
    }
}
