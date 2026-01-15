import winston from 'winston';
import 'winston-daily-rotate-file';
import path from 'path';
import fs from 'fs';
import yaml from 'js-yaml';

// Define config path
// Using absolute path based on the user's requirement: G:\项目成果打包\合同审查Agent\ContractReviewAgent\configs\pycra\logging.yaml
// In a real production env, this might need to be an env var, but for now we hardcode the relative location from project root
const CONFIG_PATH = path.resolve(process.cwd(), '../../ContractReviewAgent/configs/pycra/logging.yaml');

interface LoggingConfig {
  logging: {
    level: string;
    format: string;
    file_path: string;
    save_days: number;
    when: string;
    interval: number;
    file_handler_maxBytes: number;
    file_handler_backupCount: number;
  }
}

let logConfig: LoggingConfig['logging'] = {
    level: "INFO",
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file_path: '../../java-dev/logs/java', // Default fallback
    save_days: 7,
    when: "midnight",
    interval: 1,
    file_handler_maxBytes: 50,
    file_handler_backupCount: 100
};

try {
    if (fs.existsSync(CONFIG_PATH)) {
        const fileContents = fs.readFileSync(CONFIG_PATH, 'utf8');
        const parsed = yaml.load(fileContents) as LoggingConfig;
        if (parsed && parsed.logging) {
            logConfig = parsed.logging;
            // Override file_path to point to the java logs directory as requested by user
            // User requested: "统一到logs/java里面"
            // The config file says "cra/logs/pycra", but for frontend we want "java-dev/logs/java"
            // Let's interpret "统一到logs/java里面" as the target directory.
            // Since the user said "const LOG_DIR = ... 应该写配置文件", 
            // but the config file points to pycra logs. 
            // I will respect the user's initial prompt "统一到logs/java里面" for the directory,
            // BUT use the config file for other settings (level, rotation, etc.)
            // OR if the user means "read the path from config", we should use that.
            // However, the config path is "cra/logs/pycra". 
            // Let's assume the user wants to use the structure from config but override the path to java logs as per "统一到logs/java里面"
            
            // Actually, let's look at the user prompt again: 
            // "const LOG_DIR = ... 应该写配置文件，读取...logging.yaml"
            // This implies I should read the config. 
            // But the config says `file_path: 'cra/logs/pycra'`.
            // The user ALSO said "我想做一个日志管理，统一到logs/java里面".
            // So I will use the settings from YAML, but FORCE the directory to be the java logs directory 
            // to satisfy the "统一到logs/java里面" requirement, while using the YAML for rotation policies.
            
            // Wait, the user provided YAML snippet has: `file_path: 'G:\项目成果打包\合同审查Agent\pycra-dev\logs\pycra'` in the prompt example,
            // but the actual file content I read has `file_path: "cra/logs/pycra"`.
            // I will dynamically construct the java log path relative to the project root to be safe and correct.
            logConfig.file_path = '../../java-dev/logs/java';
        }
    }
} catch (e) {
    console.error("Failed to load logging config:", e);
}

const LOG_DIR = path.resolve(process.cwd(), logConfig.file_path);

const { combine, timestamp, printf, json } = winston.format;

// Define custom log format to match Python config: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
const customFormat = printf(({ level, message, label, timestamp }) => {
  return `${timestamp} - ${label || 'frontend'} - ${level.toUpperCase()} - ${message}`;
});

const createRotateTransport = (filename: string, levelOverride?: string) => {
  return new winston.transports.DailyRotateFile({
    filename: path.join(LOG_DIR, `${filename}-%DATE%.log`),
    datePattern: 'YYYY-MM-DD', // Matches 'midnight' / daily rotation
    zippedArchive: true,
    maxSize: `${logConfig.file_handler_maxBytes}m`, 
    maxFiles: `${logConfig.file_handler_backupCount}d`, // Keeping files for X days (backupCount approx)
    level: levelOverride || logConfig.level.toLowerCase(),
  });
};

export const logger = winston.createLogger({
  level: logConfig.level.toLowerCase(),
  format: combine(
    timestamp({
      format: 'YYYY-MM-DD HH:mm:ss,SSS' // Matches %(asctime)s
    }),
    customFormat
  ),
  transports: [
    // Console transport for dev
    new winston.transports.Console(),
    
    // Server logs
    createRotateTransport('frontend-server'),
    
    // Separate error log
    createRotateTransport('frontend-error', 'error'),
  ],
});

// Specific logger for client-side logs forwarded to server
export const clientLogger = winston.createLogger({
  level: logConfig.level.toLowerCase(),
  format: combine(
    timestamp({
      format: 'YYYY-MM-DD HH:mm:ss,SSS'
    }),
    customFormat
  ),
  transports: [
    createRotateTransport('frontend-client'),
    createRotateTransport('frontend-error', 'error'),
  ],
});
