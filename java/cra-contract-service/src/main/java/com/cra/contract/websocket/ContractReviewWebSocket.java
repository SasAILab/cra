package com.cra.contract.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import jakarta.websocket.OnClose;
import jakarta.websocket.OnError;
import jakarta.websocket.OnMessage;
import jakarta.websocket.OnOpen;
import jakarta.websocket.Session;
import jakarta.websocket.server.PathParam;
import jakarta.websocket.server.ServerEndpoint;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 合同审查实时进度推送 WebSocket
 */
@ServerEndpoint("/ws/review/{contractId}")
@Component
public class ContractReviewWebSocket {

    private static final Logger logger = LoggerFactory.getLogger(ContractReviewWebSocket.class);

    // 存储连接的 Session: contractId -> Session
    private static final Map<String, Session> sessions = new ConcurrentHashMap<>();
    
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @OnOpen
    public void onOpen(Session session, @PathParam("contractId") String contractId) {
        sessions.put(contractId, session);
        logger.info("WebSocket连接建立: contractId={}, sessionId={}", contractId, session.getId());
        sendMessage(contractId, "CONNECTION", "CONNECTED", "连接成功");
    }

    @OnClose
    public void onClose(@PathParam("contractId") String contractId) {
        sessions.remove(contractId);
        logger.info("WebSocket连接关闭: contractId={}", contractId);
    }

    @OnError
    public void onError(Session session, Throwable error) {
        logger.error("WebSocket发生错误: sessionId={}, error={}", session.getId(), error.getMessage());
    }

    @OnMessage
    public void onMessage(String message, Session session) {
        // 客户端发送消息（如果有需要处理的话）
        logger.info("收到客户端消息: {}", message);
    }

    /**
     * 推送进度消息
     * @param contractId 合同ID
     * @param step 当前步骤 (例如: OCR, KG_BUILD)
     * @param status 状态 (例如: PROCESSING, COMPLETED, FAILED)
     * @param data 数据 (可以是字符串或对象)
     */
    public static void sendMessage(String contractId, String step, String status, Object data) {
        Session session = sessions.get(contractId);
        if (session != null && session.isOpen()) {
            try {
                // 构建消息对象
                ProgressMessage message = new ProgressMessage(step, status, data);
                String jsonMessage = objectMapper.writeValueAsString(message);
                
                session.getBasicRemote().sendText(jsonMessage);
                logger.info("推送消息成功: contractId={}, step={}, status={}", contractId, step, status);
            } catch (IOException e) {
                logger.error("推送消息失败: contractId={}, error={}", contractId, e.getMessage());
            }
        } else {
            logger.debug("客户端未连接或已断开，跳过推送: contractId={}", contractId);
        }
    }

    /**
     * 内部消息类
     */
    static class ProgressMessage {
        private String step;
        private String status;
        private Object data;
        private long timestamp;

        public ProgressMessage(String step, String status, Object data) {
            this.step = step;
            this.status = status;
            this.data = data;
            this.timestamp = System.currentTimeMillis();
        }

        // Getters and Setters
        public String getStep() { return step; }
        public void setStep(String step) { this.step = step; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public Object getData() { return data; }
        public void setData(Object data) { this.data = data; }
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    }
}
