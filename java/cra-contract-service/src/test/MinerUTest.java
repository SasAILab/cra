import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class MinerUTest {

    public static void main(String[] args) {
        String inputPath = "G:\\项目成果打包\\合同审查Agent\\test_cache\\4e55aa2f-2b1d-476e-9340-e915f665b7ce_录用通知书-李子茉-亿云.pdf";
        String outputPath = "G:\\项目成果打包\\合同审查Agent";
        String mineruUrl = "http://your_ap:30000";

        try {
            String inputText = readFile(inputPath);
            String response = sendRequest(mineruUrl, inputText);
            writeFile(outputPath, response);
            System.out.println("MinerU 返回结果已写入: " + outputPath);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // 读取文件
    private static String readFile(String path) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }
        }
        return sb.toString();
    }

    // 写入文件
    private static void writeFile(String path, String content) throws IOException {
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(path))) {
            bw.write(content);
        }
    }

    // 发送 HTTP POST 请求
    private static String sendRequest(String urlString, String inputText) throws IOException {
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Content-Type", "text/plain; charset=UTF-8");
        conn.setDoOutput(true);

        // 写入请求体
        try (OutputStream os = conn.getOutputStream()) {
            os.write(inputText.getBytes("UTF-8"));
        }

        // 读取响应
        StringBuilder response = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
            String line;
            while ((line = br.readLine()) != null) {
                response.append(line).append("\n");
            }
        }

        conn.disconnect();
        return response.toString();
    }
}