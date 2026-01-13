"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft,
  FileText,
  Search,
  Share2,
  Download,
  AlertTriangle,
  Send,
  Sparkles,
  Loader2,
  Network,
} from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { contractService } from "@/services/contract";
import { ContractMain, CONTRACT_STATUS_MAP, ContractReviewMessage } from "@/types/contract";
import KnowledgeGraph from "@/components/contract/KnowledgeGraph";
import ReviewProgress from "@/components/contract/ReviewProgress";

export default function ContractDetailPage({ params }: { params: { id: string } }) {
  const [contract, setContract] = useState<ContractMain | null>(null);
  const [content, setContent] = useState<string>("");
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // WebSocket State
  const [reviewStep, setReviewStep] = useState<string>("");
  const [reviewStatus, setReviewStatus] = useState<string>("");
  const [kgData, setKgData] = useState<any>(null);
  const [docViewMode, setDocViewMode] = useState<"pdf" | "markdown">("pdf");
  const wsRef = useRef<WebSocket | null>(null);

  // Helper to transform KG data
  const transformKgData = (data: any) => {
      try {
          const backendData = data;
          const edges = backendData.edges || [];
          
          // Use a Map to collect unique nodes from edges
          const nodesMap = new Map();
          
          // Pre-populate with existing nodes if available to get metadata like types
          if (backendData.nodes) {
              backendData.nodes.forEach((item: any) => {
                   nodesMap.set(item[0], {
                       id: item[0],
                       label: item[0],
                       ...item[1]
                   });
              });
          }

          const links = edges.map((item: any) => {
              const sourceId = item[0];
              const targetId = item[1];
              const props = item[2] || {};
              
              // Ensure source and target nodes exist in our map
              if (!nodesMap.has(sourceId)) {
                  nodesMap.set(sourceId, { id: sourceId, label: sourceId, entity_type: 'UNKNOWN' });
              }
              if (!nodesMap.has(targetId)) {
                  nodesMap.set(targetId, { id: targetId, label: targetId, entity_type: 'UNKNOWN' });
              }

              // Format detailed description for tooltip
              const desc = Object.entries(props)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join('\n');

              return {
                  source: sourceId,
                  target: targetId,
                  label: props.relationship || props.type || 'relates_to', // Edge label for canvas
                  desc: desc || (props.relationship || 'relates_to'), // Tooltip content
                  ...props
              };
          });

          // Convert nodes map to array and format for graph
          const nodes = Array.from(nodesMap.values()).map((node: any) => {
              const props = node;
              // Format detailed description for tooltip
              const desc = Object.entries(props)
                  .filter(([k]) => k !== 'color' && k !== 'id' && k !== 'label') 
                  .map(([k, v]) => `${k}: ${v}`)
                  .join('\n');
              
              return {
                  ...node,
                  desc: desc || node.label,
                  color: props.entity_type === 'PERSON' ? '#3b82f6' : 
                         props.entity_type === 'CONTRACTPARTY' ? '#ef4444' : '#10b981'
              };
          });

          return { nodes, links };
      } catch (err) {
          console.error("Error transforming KG data:", err);
          return null;
      }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const id = parseInt(params.id);
        const [contractData, contentData, fileBlobUrl] = await Promise.all([
          contractService.getContractById(id),
          contractService.getContractFullContent(id),
          contractService.getContractFileBlobUrl(id)
        ]);
        setContract(contractData);
        
        // Handle Content and KG
        if (contentData) {
            // Log full content data for debugging
            console.log("Full Contract Content:", contentData);

            // Prioritize content (markdown/rich text) over plainTextContent
            setContent(contentData.content || contentData.plainTextContent || "");
            
            // Try to get KG data from various possible fields
            // Backend might return snake_case or camelCase depending on serialization
            const rawKg = (contentData as any).knowledgeGraph || (contentData as any).knowledge_graph || (contentData as any).knowledge_graph_json;
            
            if (rawKg) {
                try {
                    // If it's already an object, use it; if string, parse it
                    const parsedKg = typeof rawKg === 'string' ? JSON.parse(rawKg) : rawKg;
                    const transformed = transformKgData(parsedKg);
                    if (transformed) setKgData(transformed);
                } catch (e) {
                    console.error("Failed to parse existing KG data", e);
                }
            } else {
                console.log("No KG data found in content response, checking localStorage");
                try {
                    const cachedKg = localStorage.getItem(`contract_kg_${id}`);
                    if (cachedKg) {
                        setKgData(JSON.parse(cachedKg));
                    }
                } catch (e) {
                    console.error("Failed to load KG data from localStorage", e);
                }
            }
        }
        
        setFileUrl(fileBlobUrl);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to load contract details");
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchData();
    }
  }, [params.id]);

  useEffect(() => {
    // WebSocket Connection
    if (!params.id) return;

    // TODO: Configure WS URL properly (env variable)
    const wsUrl = `ws://localhost:8082/ws/review/${params.id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
        console.log("Connected to WebSocket");
    };

    ws.onmessage = (event) => {
        try {
            const msg: ContractReviewMessage = JSON.parse(event.data);
            console.log("WS Message:", msg);
            setReviewStep(msg.step);
            setReviewStatus(msg.status);

            if (msg.step === "OCR" && msg.status === "COMPLETED" && msg.data) {
                 // msg.data might be the content string or an object with content
                 // Prioritize content over plainTextContent
                 const newContent = typeof msg.data === 'string' ? msg.data : (msg.data.content || msg.data.plainTextContent || "");
                 if (newContent) {
                    setContent(newContent);
                    setDocViewMode("markdown"); // Auto-switch to OCR File view
                 }
            }

            if (msg.step === "KG_BUILD" && msg.status === "COMPLETED" && msg.data) {
                // Transform backend data format to react-force-graph format
                const transformed = transformKgData(msg.data);
                if (transformed) {
                     console.log("Transformed KG Data:", transformed);
                     setKgData(transformed);
                     // Cache KG data in localStorage for persistence
                     try {
                        localStorage.setItem(`contract_kg_${params.id}`, JSON.stringify(transformed));
                     } catch (err) {
                        console.error("Failed to save KG data to localStorage", err);
                     }
                }
            }
        } catch (e) {
            console.error("Failed to parse WS message", e);
        }
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
    };

    return () => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    };
  }, [params.id]);

  useEffect(() => {
    return () => {
        if (fileUrl) URL.revokeObjectURL(fileUrl);
    };
  }, [fileUrl]);

  const handleStartReview = async () => {
    if (!contract) return;
    try {
        await contractService.reviewContract(contract);
        // Status updates will come via WebSocket
    } catch (e) {
        console.error("Failed to start review", e);
        // You might want to show a toast here
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !contract) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error || "Contract not found"}</p>
        <Link href="/contracts">
          <Button variant="outline">Back to Contracts</Button>
        </Link>
      </div>
    );
  }

  const statusConfig = CONTRACT_STATUS_MAP[contract.status] || { label: "Unknown", variant: "default" };
  const formattedDate = contract.updateTime 
    ? new Date(contract.updateTime).toLocaleString() 
    : (contract.createTime ? new Date(contract.createTime).toLocaleString() : "N/A");

  return (
    <div className="flex flex-col h-[calc(100vh-theme(spacing.20))] gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-4">
          <Link href="/contracts">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
              {contract.contractName} <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
            </h1>
            <p className="text-sm text-muted-foreground">
              ID: {contract.id} • Type: {contract.category || "General"} • Last updated: {formattedDate}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Share2 className="mr-2 h-4 w-4" /> Share
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" /> Export
          </Button>
          <Button size="sm" onClick={handleStartReview} disabled={reviewStatus === "PROCESSING"}>
             {reviewStatus === "PROCESSING" ? (
                 <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {reviewStep === "OCR" ? "OCR Processing..." : 
                     reviewStep === "KG_BUILD" ? "Building Graph..." : 
                     "Reviewing..."}
                 </>
             ) : (
                "Start AI Review"
             )}
          </Button>
        </div>
      </div>

      {/* Review Progress Indicator - Full Width */}
      {(reviewStatus === "PROCESSING" || reviewStep) && (
          <div className="w-full">
              <ReviewProgress currentStep={reviewStep} status={reviewStatus} />
          </div>
      )}

      {/* Main Content Split View */}
      <div className="flex flex-1 gap-6 overflow-hidden items-start">
        {/* Document Viewer (Left) */}
        <Card className="w-[45%] flex flex-col overflow-hidden h-full">
          <CardHeader className="py-3 border-b flex flex-row items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                <span>Document View</span>
            </div>
             <div className="flex items-center gap-2">
                <div className="flex items-center bg-muted rounded-lg p-1">
                    <Button 
                        variant={docViewMode === "pdf" ? "default" : "ghost"} 
                        size="sm" 
                        className="h-7 text-xs px-2"
                        onClick={() => setDocViewMode("pdf")}
                    >
                        Original File
                    </Button>
                    <Button 
                        variant={docViewMode === "markdown" ? "default" : "ghost"} 
                        size="sm" 
                        className="h-7 text-xs px-2"
                        onClick={() => setDocViewMode("markdown")}
                    >
                        OCR File
                    </Button>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Search className="h-4 w-4" />
                </Button>
             </div>
          </CardHeader>
          <div className="flex-1 overflow-hidden bg-muted/20 relative">
             {docViewMode === "pdf" ? (
                 fileUrl ? (
                     <iframe 
                        src={fileUrl} 
                        className="w-full h-full border-none"
                        title="Contract PDF"
                        onError={() => console.error("Iframe failed to load PDF")}
                     />
                 ) : (
                    <div className="flex-1 overflow-auto p-8 h-full flex items-center justify-center">
                        <div className="text-center space-y-4 max-w-md">
                            <div className="p-4 rounded-full bg-muted inline-flex">
                                <FileText className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <div>
                                <h3 className="text-lg font-medium">Document Preview Unavailable</h3>
                                <p className="text-sm text-muted-foreground mt-1">
                                    We couldn't load the PDF preview. This might be because the file is missing or you don't have permission to view it.
                                </p>
                            </div>
                            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                                Try Reloading
                            </Button>
                        </div>
                    </div>
                 )
             ) : (
                 <div className="flex-1 overflow-auto h-full bg-background p-8">
                     {content ? (
                         <div className="prose prose-sm max-w-none dark:prose-invert">
                            <ReactMarkdown>{content}</ReactMarkdown>
                         </div>
                     ) : (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                            <FileText className="h-12 w-12 mb-4 opacity-20" />
                            <p>No OCR content available yet.</p>
                            <p className="text-xs mt-1">Start the AI review to generate content.</p>
                        </div>
                     )}
                 </div>
             )}
          </div>
        </Card>

        {/* AI Assistant (Right) */}
        <Card className="flex-1 flex flex-col overflow-hidden">
            <Tabs defaultValue="risks" className="flex flex-col overflow-hidden flex-1">
                <div className="px-4 py-2 border-b shrink-0 bg-background z-10">
                    <TabsList className="w-full">
                        <TabsTrigger value="risks" className="flex-1">Risks (3)</TabsTrigger>
                        <TabsTrigger value="suggestions" className="flex-1">Suggestions</TabsTrigger>
                        <TabsTrigger value="graph" className="flex-1">Graph</TabsTrigger>
                        <TabsTrigger value="chat" className="flex-1">Assistant</TabsTrigger>
                    </TabsList>
                </div>

                <TabsContent value="risks" className="overflow-auto p-4 m-0 space-y-4 flex-1">
                    <div className="space-y-4">
                        <Card className="border-destructive/50 bg-destructive/5">
                            <CardHeader className="p-3 pb-2">
                                <CardTitle className="text-sm font-medium flex items-center gap-2 text-destructive">
                                    <AlertTriangle className="h-4 w-4" />
                                    Unbalanced Termination
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-3 pt-0 text-xs text-muted-foreground">
                                Clause 5 allows Client to terminate for convenience but restricts Provider. Recommended: Mutual termination for convenience.
                            </CardContent>
                        </Card>
                         <Card className="border-orange-200 bg-orange-50 dark:bg-orange-900/20 dark:border-orange-800">
                            <CardHeader className="p-3 pb-2">
                                <CardTitle className="text-sm font-medium flex items-center gap-2 text-orange-600 dark:text-orange-400">
                                    <AlertTriangle className="h-4 w-4" />
                                    Short Confidentiality Term
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-3 pt-0 text-xs text-muted-foreground">
                                Clause 3 limits confidentiality to 2 years. Standard for this industry is 5 years.
                            </CardContent>
                        </Card>
                         <Card className="border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-800">
                            <CardHeader className="p-3 pb-2">
                                <CardTitle className="text-sm font-medium flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                                    <AlertTriangle className="h-4 w-4" />
                                    Missing Mutual Indemnification
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-3 pt-0 text-xs text-muted-foreground">
                                Clause 4 only indemnifies the Client. Consider adding mutual indemnification.
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="suggestions" className="overflow-auto p-4 m-0 flex-1">
                     <div className="space-y-4">
                        <div className="border rounded-lg p-3 bg-background">
                            <div className="flex items-center gap-2 mb-2">
                                <Sparkles className="h-4 w-4 text-primary" />
                                <span className="text-sm font-medium">Clause 3 Rewrite</span>
                            </div>
                            <p className="text-xs text-muted-foreground mb-2">
                                "Provider agrees to keep all Client information confidential. This obligation survives the termination of this Agreement for a period of 5 years, and indefinitely for trade secrets."
                            </p>
                            <Button size="sm" variant="outline" className="w-full h-7 text-xs">Apply Change</Button>
                        </div>
                     </div>
                </TabsContent>

                <TabsContent value="graph" className="flex flex-col p-0 m-0 overflow-hidden bg-background flex-1">
                    <KnowledgeGraph data={kgData} />
                </TabsContent>

                <TabsContent value="chat" className="flex flex-col p-0 m-0 bg-background flex-1">
                    <div className="flex-1 overflow-auto p-4 space-y-4">
                        <div className="flex gap-3 text-sm">
                             <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                <Sparkles className="h-4 w-4 text-primary" />
                             </div>
                             <div className="bg-muted p-3 rounded-lg rounded-tl-none">
                                <p>I've analyzed the contract. There are 3 high-risk clauses requiring your attention. Would you like me to draft a revision for the Termination clause?</p>
                             </div>
                        </div>
                        <div className="flex gap-3 text-sm flex-row-reverse">
                             <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 text-primary-foreground">
                                JD
                             </div>
                             <div className="bg-primary text-primary-foreground p-3 rounded-lg rounded-tr-none">
                                <p>Yes, please draft a mutual termination clause.</p>
                             </div>
                        </div>
                    </div>
                    <div className="p-4 border-t">
                        <form className="flex gap-2">
                            <Input placeholder="Ask AI about this contract..." />
                            <Button size="icon" type="submit">
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                    </div>
                </TabsContent>
            </Tabs>
        </Card>
      </div>
    </div>
  );
}
