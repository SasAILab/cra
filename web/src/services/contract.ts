import { apiFetch, CONTRACT_SERVICE_URL } from "@/lib/api";
import { ContractContent, ContractMain } from "@/types/contract";
import { useAuthStore } from "@/store/auth";

export const contractService = {
  uploadSingle: async (file: File, category: string, department: string): Promise<ContractMain> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    formData.append("department", department);
    const token = useAuthStore.getState().token || undefined;
    
    const res = await apiFetch("/upload/single", {
      method: "POST",
      body: formData,
    }, token, CONTRACT_SERVICE_URL);
    
    if (res.code !== 200) {
        throw new Error(res.message || "Upload failed");
    }
    return res.data;
  },

  uploadBatch: async (files: File[], category: string, department: string): Promise<ContractMain[]> => {
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    formData.append("category", category);
    formData.append("department", department);
    
    const token = useAuthStore.getState().token || undefined;

    const res = await apiFetch("/upload/batch", {
      method: "POST",
      body: formData,
    }, token, CONTRACT_SERVICE_URL);

    if (res.code !== 200) {
        throw new Error(res.message || "Batch upload failed");
    }
    return res.data;
  },

  fetchContracts: async (page = 0, size = 10, params = {}): Promise<{ list: ContractMain[], total: number }> => {
    const token = useAuthStore.getState().token || undefined;
    const queryParams = new URLSearchParams({
      page: page.toString(), // Backend expects 0-indexed page
      size: size.toString(),
      ...params
    });
    
    // Backend: @GetMapping
    const res = await apiFetch(`/?${queryParams.toString()}`, {}, token, CONTRACT_SERVICE_URL);
    
    if (res.code !== 200) {
      throw new Error(res.message || "Fetch contracts failed");
    }

    const data = res.data;
    let list: ContractMain[] = [];
    let total = 0;

    // Backend returns Page<ContractMain>
    // Spring Page structure usually has 'content' for list and 'totalElements' for count
    if (data && Array.isArray(data.content)) {
        list = data.content;
        total = data.totalElements;
    } else if (Array.isArray(data)) {
        // Fallback or different structure
        list = data;
        total = data.length;
    } else {
        // Fallback for MyBatis Page or similar if structure differs
        list = data?.list || data?.records || [];
        total = data?.total || list.length || 0;
    }
    
    return { list, total };
  },
  
  deleteContract: async (id: number): Promise<void> => {
      const token = useAuthStore.getState().token || undefined;
      // Backend: @DeleteMapping("/{id}")
      const res = await apiFetch(`/${id}`, {
          method: "DELETE"
      }, token, CONTRACT_SERVICE_URL);
      
      if (res.code !== 200) {
          throw new Error(res.message || "Delete failed");
      }
  },

  getContractById: async (id: number): Promise<ContractMain> => {
    const token = useAuthStore.getState().token || undefined;
    // Backend: @GetMapping("/{id}")
    const res = await apiFetch(`/${id}`, {}, token, CONTRACT_SERVICE_URL);

    if (res.code !== 200) {
        throw new Error(res.message || "Get contract failed");
    }
    return res.data;
  },

  getContractFileBlobUrl: async (contractId: number): Promise<string | null> => {
      const token = useAuthStore.getState().token || undefined;
      const url = `${CONTRACT_SERVICE_URL}/${contractId}/file`;
      
      try {
          const headers: HeadersInit = {};
          if (token) {
              headers['Authorization'] = `Bearer ${token}`;
          }
          
          const response = await fetch(url, {
              headers
          });
          
          if (!response.ok) return null;
          
          const blob = await response.blob();
          return URL.createObjectURL(blob);
      } catch (e) {
          console.error("Failed to fetch PDF", e);
          return null;
      }
  },

  getContractContent: async (contractId: number): Promise<string> => {
    const token = useAuthStore.getState().token || undefined;
    const res = await apiFetch(`/${contractId}/content`, {}, token, CONTRACT_SERVICE_URL);

    if (res.code !== 200) {
       console.warn("Failed to fetch contract content", res);
       return "";
    }
    if (typeof res.data === 'string') return res.data;
    // Prioritize content over plainTextContent
    return res.data?.content || res.data?.plainTextContent || "";
  },

  getContractFullContent: async (contractId: number): Promise<ContractContent | null> => {
    const token = useAuthStore.getState().token || undefined;
    const res = await apiFetch(`/${contractId}/content`, {}, token, CONTRACT_SERVICE_URL);

    if (res.code !== 200) {
       console.warn("Failed to fetch contract content", res);
       return null;
    }
    // If backend returns string directly, wrap it in ContractContent object
    if (typeof res.data === 'string') {
      return {
        content: res.data,
        plainTextContent: res.data
      } as unknown as ContractContent;
    }
    return res.data as ContractContent;
  },

  updateContract: async (id: number, contract: Partial<ContractMain>): Promise<ContractMain> => {
    const token = useAuthStore.getState().token || undefined;
    // Backend: @PutMapping("/{id}")
    const res = await apiFetch(`/${id}`, {
        method: "PUT",
        body: JSON.stringify(contract)
    }, token, CONTRACT_SERVICE_URL);

    if (res.code !== 200) {
        throw new Error(res.message || "Update contract failed");
    }
    return res.data;
  },

  reviewContract: async (contract: ContractMain): Promise<ContractMain> => {
    const token = useAuthStore.getState().token || undefined;
    const res = await apiFetch("/agent/review", {
        method: "POST",
        body: JSON.stringify(contract)
    }, token, CONTRACT_SERVICE_URL);

    if (res.code !== 200) {
        throw new Error(res.message || "Review contract failed");
    }
    return res.data;
  }
};
