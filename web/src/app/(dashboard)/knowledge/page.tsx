import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  Search,
  FileText,
  Tag,
  Clock,
  ArrowRight,
  Folder,
} from "lucide-react";

export default function KnowledgePage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground">
            Access legal templates, clauses, and compliance guidelines.
          </p>
        </div>
        <Button>
          <BookOpen className="mr-2 h-4 w-4" /> Contribute
        </Button>
      </div>

      {/* Search Section */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
        <Input
          placeholder="Search for templates, clauses, or legal terms..."
          className="pl-10 h-12 text-lg"
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Categories */}
        <Card className="col-span-full">
            <CardHeader>
                <CardTitle>Categories</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex gap-4 overflow-x-auto pb-2">
                    {[
                        { name: "Standard Clauses", count: 128 },
                        { name: "Contract Templates", count: 45 },
                        { name: "Legal Guidelines", count: 23 },
                        { name: "Compliance Policies", count: 12 },
                        { name: "Case Studies", count: 8 },
                    ].map((category, i) => (
                        <div key={i} className="flex items-center gap-3 p-4 border rounded-lg min-w-[200px] hover:bg-accent cursor-pointer transition-colors">
                            <div className="p-2 bg-primary/10 rounded-md text-primary">
                                <Folder className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="font-medium text-sm">{category.name}</p>
                                <p className="text-xs text-muted-foreground">{category.count} items</p>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>

        {/* Popular Templates */}
        <div className="lg:col-span-2 space-y-6">
             <h2 className="text-xl font-semibold tracking-tight">Popular Resources</h2>
             <div className="grid gap-4">
                {[
                    { title: "Standard NDA Template 2024", type: "Template", downloads: "2.4k", date: "Jan 1, 2024" },
                    { title: "GDPR Data Processing Addendum", type: "Clause", downloads: "1.8k", date: "Dec 15, 2023" },
                    { title: "Software SaaS Agreement", type: "Template", downloads: "1.2k", date: "Nov 20, 2023" },
                    { title: "Employee IP Assignment", type: "Clause", downloads: "980", date: "Oct 5, 2023" },
                ].map((item, i) => (
                    <Card key={i} className="hover:shadow-md transition-shadow cursor-pointer">
                        <CardContent className="p-4 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-muted rounded-md">
                                    <FileText className="h-6 w-6 text-muted-foreground" />
                                </div>
                                <div>
                                    <h3 className="font-semibold">{item.title}</h3>
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                                        <Badge variant="secondary" className="text-[10px] h-5">{item.type}</Badge>
                                        <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {item.date}</span>
                                        <span>•</span>
                                        <span>{item.downloads} downloads</span>
                                    </div>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon">
                                <ArrowRight className="h-4 w-4" />
                            </Button>
                        </CardContent>
                    </Card>
                ))}
             </div>
        </div>

        {/* Recent Updates */}
        <div className="space-y-6">
            <h2 className="text-xl font-semibold tracking-tight">Recent Updates</h2>
            <Card>
                <CardContent className="p-0">
                    <div className="divide-y">
                        {[
                            { title: "Updated Liability Cap Clause", desc: "Reflects new insurance requirements.", time: "2 hours ago" },
                            { title: "New California Privacy Policy", desc: "Compliance with CPRA amendments.", time: "Yesterday" },
                            { title: "Freelance Contract V2.0", desc: "Added IP transfer section.", time: "2 days ago" },
                        ].map((update, i) => (
                            <div key={i} className="p-4 hover:bg-muted/50 transition-colors">
                                <div className="flex items-start gap-3">
                                    <div className="mt-1">
                                        <Tag className="h-4 w-4 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium">{update.title}</p>
                                        <p className="text-xs text-muted-foreground mt-1">{update.desc}</p>
                                        <p className="text-[10px] text-muted-foreground mt-2">{update.time}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
      </div>
    </div>
  );
}
