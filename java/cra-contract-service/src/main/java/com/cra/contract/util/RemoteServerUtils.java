package com.cra.contract.util;

import com.jcraft.jsch.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import java.util.Vector;

@Component
public class RemoteServerUtils {

    private static final Logger logger = LoggerFactory.getLogger(RemoteServerUtils.class);

    @Value("${remote.host}")
    private String host;

    @Value("${remote.port:22}")
    private int port;

    @Value("${remote.username}")
    private String username;

    @Value("${remote.password}")
    private String password;

    /**
     * 上传文件到远程服务器
     * @param inputStream 本地文件流
     * @param remotePath 远程目录
     * @param fileName 文件名
     * @return 远程文件的完整路径
     */
    public String uploadFile(InputStream inputStream, String remotePath, String fileName) throws Exception {
        Session session = null;
        ChannelSftp channelSftp = null;
        try {
            session = createSession();
            channelSftp = (ChannelSftp) session.openChannel("sftp");
            channelSftp.connect();
            try {
                channelSftp.cd(remotePath);
            } catch (SftpException e) {
                createDir(channelSftp, remotePath);
                channelSftp.cd(remotePath);
            }

            channelSftp.put(inputStream, fileName);
            String fullPath = remotePath.endsWith("/") ? remotePath + fileName : remotePath + "/" + fileName;
            logger.info("文件上传成功: {}", fullPath);
            return fullPath;
        } finally {
            closeChannel(channelSftp);
            closeSession(session);
        }
    }

    /**
     * 删除远程文件
     * @param remoteFilePath 远程文件完整路径
     */
    public void deleteFile(String remoteFilePath) {
        Session session = null;
        ChannelSftp channelSftp = null;
        try {
            session = createSession();
            channelSftp = (ChannelSftp) session.openChannel("sftp");
            channelSftp.connect();
            channelSftp.rm(remoteFilePath);
            logger.info("远程文件已删除: {}", remoteFilePath);
        } catch (Exception e) {
            logger.error("删除远程文件失败: {}", e.getMessage());
        } finally {
            closeChannel(channelSftp);
            closeSession(session);
        }
    }

    
    /**
     * 检查远程文件是否存在
     */
    public boolean exists(String remoteFilePath) {
        Session session = null;
        ChannelSftp channelSftp = null;
        try {
            session = createSession();
            channelSftp = (ChannelSftp) session.openChannel("sftp");
            channelSftp.connect();
            channelSftp.lstat(remoteFilePath);
            return true;
        } catch (Exception e) {
            return false;
        } finally {
            closeChannel(channelSftp);
            closeSession(session);
        }
    }
    
    /**
     * 下载远程文件到本地文件
     */
    public void downloadFile(String remoteFilePath, File localFile) throws Exception {
        Session session = null;
        ChannelSftp channelSftp = null;
        try {
            session = createSession();
            channelSftp = (ChannelSftp) session.openChannel("sftp");
            channelSftp.connect();
            
            try (java.io.FileOutputStream fos = new java.io.FileOutputStream(localFile)) {
                channelSftp.get(remoteFilePath, fos);
            }
            logger.info("文件下载成功: {} -> {}", remoteFilePath, localFile.getAbsolutePath());
        } finally {
            closeChannel(channelSftp);
            closeSession(session);
        }
    }

    /**
     * 递归创建远程目录
     * @param remotePath 远程目录路径
     */
    public void createRemoteDir(String remotePath) throws Exception {
        Session session = null;
        ChannelSftp channelSftp = null;
        try {
            session = createSession();
            channelSftp = (ChannelSftp) session.openChannel("sftp");
            channelSftp.connect();
            createDir(channelSftp, remotePath);
            logger.info("远程目录检查/创建成功: {}", remotePath);
        } finally {
            closeChannel(channelSftp);
            closeSession(session);
        }
    }

    private Session createSession() throws JSchException {
        JSch jsch = new JSch();
        Session session = jsch.getSession(username, host, port);
        session.setPassword(password);
        Properties config = new Properties();
        config.put("StrictHostKeyChecking", "no");
        session.setConfig(config);
        session.connect();
        return session;
    }

    private void closeChannel(Channel channel) {
        if (channel != null && channel.isConnected()) {
            channel.disconnect();
        }
    }

    private void closeSession(Session session) {
        if (session != null && session.isConnected()) {
            session.disconnect();
        }
    }
    
    private void createDir(ChannelSftp sftp, String path) throws SftpException {
        String[] folders = path.split("/");
        String currentPath = "";
        if (path.startsWith("/")) {
            currentPath = "/";
        }
        for (String folder : folders) {
            if (folder.length() > 0) {
                try {
                    sftp.cd(currentPath + folder);
                    currentPath += folder + "/";
                } catch (SftpException e) {
                    sftp.mkdir(currentPath + folder);
                    sftp.cd(currentPath + folder);
                    currentPath += folder + "/";
                }
            }
        }
    }
}
