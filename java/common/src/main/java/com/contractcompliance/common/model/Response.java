package com.contractcompliance.common.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Response<T> {
    /**
     * 响应状态码
     */
    private int code;

    /**
     * 响应消息
     */
    private String message;

    /**
     * 响应数据
     */
    private T data;

    /**
     * 时间戳
     */
    private long timestamp;

    public Response() {
        this.timestamp = System.currentTimeMillis();
    }

    public Response(int code, String message) {
        this();
        this.code = code;
        this.message = message;
    }

    public Response(int code, String message, T data) {
        this(code, message);
        this.data = data;
    }

    // 成功响应
    public static <T> Response<T> success() {
        return new Response<>(200, "操作成功");
    }

    public static <T> Response<T> success(T data) {
        return new Response<>(200, "操作成功", data);
    }

    public static <T> Response<T> success(String message, T data) {
        return new Response<>(200, message, data);
    }

    // 失败响应
    public static <T> Response<T> fail() {
        return new Response<>(500, "操作失败");
    }

    public static <T> Response<T> fail(String message) {
        return new Response<>(500, message);
    }

    public static <T> Response<T> fail(int code, String message) {
        return new Response<>(code, message);
    }

    public static <T> Response<T> fail(int code, String message, T data) {
        return new Response<>(code, message, data);
    }
}