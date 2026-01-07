import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
  ArrowRight,
  MoreHorizontal,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your contract compliance status and recent activities.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Contract
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Contracts
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,248</div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pending Review
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">
              4 urgent reviews needed
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">7</div>
            <p className="text-xs text-muted-foreground">
              High risk clauses detected
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Compliance Rate
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">94.2%</div>
            <p className="text-xs text-muted-foreground">
              +2.1% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Contracts */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Contracts</CardTitle>
            <CardDescription>
              You have 24 contracts pending review.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                {
                  id: "CN-2024-001",
                  name: "Service Agreement - TechCorp",
                  status: "In Progress",
                  risk: "Medium",
                  date: "Today, 10:23 AM",
                },
                {
                  id: "CN-2024-002",
                  name: "NDA - Innovation Labs",
                  status: "Completed",
                  risk: "Low",
                  date: "Yesterday, 2:15 PM",
                },
                {
                  id: "CN-2024-003",
                  name: "License Agreement - SoftSys",
                  status: "Pending",
                  risk: "High",
                  date: "Jan 4, 2024",
                },
                {
                  id: "CN-2024-004",
                  name: "Employment Contract - J. Doe",
                  status: "Completed",
                  risk: "Low",
                  date: "Jan 3, 2024",
                },
                {
                  id: "CN-2024-005",
                  name: "Vendor Agreement - SupplyCo",
                  status: "Review",
                  risk: "Medium",
                  date: "Jan 2, 2024",
                },
              ].map((contract, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {contract.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {contract.id} • {contract.date}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge
                      variant={
                        contract.risk === "High"
                          ? "destructive"
                          : contract.risk === "Medium"
                          ? "secondary" // Changed from warning (not in standard variants) to secondary for now, or I should add warning variant
                          : "outline"
                      }
                    >
                      {contract.risk} Risk
                    </Badge>
                    <Badge
                        variant={
                            contract.status === "Completed" ? "success" : "secondary"
                        }
                    >
                        {contract.status}
                    </Badge>
                    <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions / Insights */}
        <div className="col-span-3 space-y-4">
            <Card>
                <CardHeader>
                    <CardTitle>AI Insights</CardTitle>
                    <CardDescription>Latest analysis from the compliance engine</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="rounded-lg border p-3 bg-muted/50">
                        <div className="flex items-center gap-2 mb-2">
                            <TrendingUp className="h-4 w-4 text-primary" />
                            <span className="text-sm font-semibold">Trend Detected</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Indemnity clauses in recent software agreements are stricter than standard policy.
                        </p>
                    </div>
                    <div className="rounded-lg border p-3 bg-muted/50">
                         <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                            <span className="text-sm font-semibold">Policy Update Required</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            New data privacy regulations may affect 15 active contracts.
                        </p>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-2">
                    <Button variant="outline" className="justify-start">
                        <FileText className="mr-2 h-4 w-4" />
                        Draft New Template
                    </Button>
                    <Button variant="outline" className="justify-start">
                        <Clock className="mr-2 h-4 w-4" />
                        Review Pending Items
                    </Button>
                    <Button variant="outline" className="justify-start">
                        <ArrowRight className="mr-2 h-4 w-4" />
                        Generate Compliance Report
                    </Button>
                </CardContent>
            </Card>
        </div>
      </div>
    </div>
  );
}
