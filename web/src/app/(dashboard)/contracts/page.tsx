import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  FileText,
  Search,
  Filter,
  MoreHorizontal,
  Plus,
} from "lucide-react";
import Link from "next/link";

export default function ContractsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Contracts</h1>
          <p className="text-muted-foreground">
            Manage and review your contracts.
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> Upload Contract
        </Button>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle>All Contracts</CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="search"
                placeholder="Search..."
                className="w-[200px] rounded-md border border-input bg-background pl-9 pr-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contract Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Risk Level</TableHead>
                  <TableHead>Last Modified</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  {
                    id: "1",
                    name: "Service Agreement - TechCorp",
                    type: "Service",
                    status: "In Progress",
                    risk: "Medium",
                    date: "2024-01-05",
                  },
                  {
                    id: "2",
                    name: "NDA - Innovation Labs",
                    type: "NDA",
                    status: "Completed",
                    risk: "Low",
                    date: "2024-01-04",
                  },
                  {
                    id: "3",
                    name: "License Agreement - SoftSys",
                    type: "License",
                    status: "Pending Review",
                    risk: "High",
                    date: "2024-01-04",
                  },
                ].map((contract) => (
                  <TableRow key={contract.id}>
                    <TableCell className="font-medium">
                        <Link href={`/contracts/${contract.id}`} className="hover:underline flex items-center gap-2">
                             <FileText className="h-4 w-4 text-muted-foreground" />
                             {contract.name}
                        </Link>
                    </TableCell>
                    <TableCell>{contract.type}</TableCell>
                    <TableCell>
                      <Badge variant={contract.status === "Completed" ? "success" : "secondary"}>
                        {contract.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                        <Badge variant={contract.risk === "High" ? "destructive" : contract.risk === "Medium" ? "secondary" : "outline"}>
                            {contract.risk}
                        </Badge>
                    </TableCell>
                    <TableCell>{contract.date}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
