import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  PenTool,
  Save,
  Play,
  FileText,
  CheckCircle,
  Eye,
  RotateCcw,
} from "lucide-react";

export default function DraftingPage() {
  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-theme(spacing.20))]">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Contract Drafting</h1>
          <p className="text-muted-foreground">
            Generate contracts using AI templates and smart clauses.
          </p>
        </div>
      </div>

      <div className="flex gap-6 h-full overflow-hidden">
        {/* Configuration Panel */}
        <div className="w-[400px] flex flex-col gap-4 overflow-auto">
          <Card>
            <CardHeader>
              <CardTitle>Template Selection</CardTitle>
              <CardDescription>
                Choose a template to start drafting.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Contract Type
                </label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select contract type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="nda">Non-Disclosure Agreement (NDA)</SelectItem>
                    <SelectItem value="service">Service Agreement</SelectItem>
                    <SelectItem value="employment">Employment Contract</SelectItem>
                    <SelectItem value="license">Software License</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                 <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Jurisdiction
                </label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select jurisdiction" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ca">California, USA</SelectItem>
                    <SelectItem value="ny">New York, USA</SelectItem>
                    <SelectItem value="uk">United Kingdom</SelectItem>
                    <SelectItem value="cn">China</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="flex-1">
             <CardHeader>
              <CardTitle>Key Terms</CardTitle>
              <CardDescription>
                Define the essential terms for the contract.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium">Party A (Client)</label>
                    <Input placeholder="Enter company name" />
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium">Party B (Provider)</label>
                    <Input placeholder="Enter company name" />
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium">Effective Date</label>
                    <Input type="date" />
                </div>
                 <div className="space-y-2">
                    <label className="text-sm font-medium">Term Duration</label>
                    <Input placeholder="e.g. 1 year, Indefinite" />
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium">Payment Terms</label>
                    <Textarea placeholder="e.g. $100/hr, Net 30" className="min-h-[100px]" />
                </div>
                <Button className="w-full">
                    <Play className="mr-2 h-4 w-4" /> Generate Draft
                </Button>
            </CardContent>
          </Card>
        </div>

        {/* Preview Panel */}
        <div className="flex-1 flex flex-col gap-4 overflow-hidden">
             <Card className="flex-1 flex flex-col overflow-hidden">
                <CardHeader className="py-3 border-b flex flex-row items-center justify-between">
                    <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary" />
                        <span className="font-semibold">Draft Preview</span>
                        <Badge variant="secondary" className="ml-2">Auto-Generated</Badge>
                    </div>
                    <div className="flex items-center gap-2">
                         <Button variant="ghost" size="sm">
                            <RotateCcw className="mr-2 h-3 w-3" /> Reset
                        </Button>
                        <Button variant="outline" size="sm">
                            <Eye className="mr-2 h-3 w-3" /> Preview PDF
                        </Button>
                         <Button size="sm">
                            <Save className="mr-2 h-3 w-3" /> Save Draft
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-auto p-8 bg-muted/20">
                     <div className="mx-auto max-w-3xl bg-background shadow-sm p-12 min-h-full border">
                         <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-4">
                            <PenTool className="h-12 w-12 opacity-20" />
                            <p>Select a template and fill in the terms to generate a draft.</p>
                         </div>
                     </div>
                </CardContent>
             </Card>

             {/* Compliance Check (Mini) */}
             <Card className="h-[150px] shrink-0">
                <CardHeader className="py-3 border-b">
                    <CardTitle className="text-sm flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Real-time Compliance Check
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                    <p className="text-sm text-muted-foreground">
                        Compliance checks will run automatically as you edit the draft.
                    </p>
                </CardContent>
             </Card>
        </div>
      </div>
    </div>
  );
}
