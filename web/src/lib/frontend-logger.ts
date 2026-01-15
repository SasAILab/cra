type LogLevel = 'info' | 'warn' | 'error' | 'debug';

interface LogPayload {
  level: LogLevel;
  message: string;
  meta?: any;
}

const sendLog = async (payload: LogPayload) => {
  try {
    await fetch('/api/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    // Fallback to console if API fails
    console.error('Failed to send log to server:', err);
  }
};

export const frontendLogger = {
  info: (message: string, meta?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[INFO] ${message}`, meta || '');
    }
    sendLog({ level: 'info', message, meta });
  },
  warn: (message: string, meta?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.warn(`[WARN] ${message}`, meta || '');
    }
    sendLog({ level: 'warn', message, meta });
  },
  error: (message: string, meta?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.error(`[ERROR] ${message}`, meta || '');
    }
    sendLog({ level: 'error', message, meta });
  },
  debug: (message: string, meta?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[DEBUG] ${message}`, meta || '');
    }
    // Optional: Don't send debug logs to production server to save bandwidth
    // sendLog({ level: 'debug', message, meta }); 
  },
};
