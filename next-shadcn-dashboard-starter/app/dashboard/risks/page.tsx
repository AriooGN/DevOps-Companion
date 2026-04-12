"use client"

import * as React from "react"
import {
    ColumnDef,
    ColumnFiltersState,
    SortingState,
    VisibilityState,
    flexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown, MoreHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { useEffect, useState, useRef } from "react"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import PageContainer from "@/components/layout/page-container"
import { Risk } from "@/constants/data"
import { useSession } from "next-auth/react"
import { set } from "date-fns"
import { CellAction } from './_components/risk-tables/cell-action';
import { flaskApiUrl } from '@/lib/flask-api';

export const columns: ColumnDef<Risk>[] = [
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={
                    table.getIsAllPageRowsSelected() ||
                    (table.getIsSomePageRowsSelected() && "indeterminate")
                }
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                aria-label="Select all"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
            />
        ),
        enableSorting: false,
        enableHiding: false,
    },
    {
        accessorKey: "id",
        header: "ID",
        cell: ({ row }) => <div>{row.getValue("id")}</div>,
    },
    {
        accessorKey: "title",
        header: "Title",
        cell: ({ row }) => row.getValue("title")
    },
    {
        accessorKey: "state",
        header: "State",
        cell: ({ row }) => row.getValue("state")
    },
    {
        accessorKey: "assignedTo",
        header: "Assigned To",
        cell: ({ row }) => {
            const assignedTo = row.getValue("assignedTo");
            return assignedTo ? (
                assignedTo
            ) : (
                <div className=" font-weight-bold" style={{ fontWeight: "bold" }}>
                    ---
                </div>
            );
        },
    },
    {
        accessorKey: "userEmail",
        header: "User Email",
        cell: ({ row }) => {
            const userEmail = row.getValue("userEmail");
            return userEmail ? (
                userEmail
            ) : (
                <div className=" font-weight-bold" style={{ fontWeight: "bold" }}>
                    ---
                </div>
            );
        },
    },
    {
        accessorKey: "dueDate",
        header: "Due Date",
        cell: ({ row }) => {
            const dueDate = row.getValue("dueDate");
            if (!dueDate) {
                return (
                    <div className=" font-weight-bold" style={{ fontWeight: "bold" }}>
                        ---
                    </div>
                );
            }
    
            const date = new Date(dueDate as string | number | Date);
            return isNaN(date.getTime()) ? (
                <div className=" font-weight-bold" style={{ fontWeight: "bold" }}>
                    ---
                </div>
            ) : (
                <div className="">{date.toLocaleDateString("en-US")}</div>
            );
        },
    },
    {
        accessorKey: "priorityScore",
        header: ({ column }) => {
            return (<Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            >
                Priority Score
                <ArrowUpDown />
            </Button>)
        },
        cell: ({ row }) => <div>{row.getValue("priorityScore")}</div>,

    },
    {
        id: 'actions',
        cell: ({ row }) => <CellAction data={row.original} />
      }
    // {
    //     id: "actions",
    //     enableHiding: false,
    //     cell: ({ row }) => {
    //         const payment = row.original
    //         const { data: session } = useSession();

    //         return (
    //             <DropdownMenu>
    //                 <DropdownMenuTrigger asChild>
    //                     <Button variant="ghost" className="h-8 w-8 p-0">
    //                         <span className="sr-only">Open menu</span>
    //                         <MoreHorizontal />
    //                     </Button>
    //                 </DropdownMenuTrigger>
    //                 <DropdownMenuContent align="end">
    //                     <DropdownMenuLabel>Actions</DropdownMenuLabel>
    //                     <DropdownMenuItem >Send Email about task</DropdownMenuItem>
    //                     <DropdownMenuItem onClick={() => handleFollowUpEmail(row, session)}>Send Follow-up Email to asignee</DropdownMenuItem>
    //                 </DropdownMenuContent>
    //             </DropdownMenu>
    //         )
    //     },
    // },

]

// const handleFollowUpEmail = async (row: any, session: any) => {
//     try {
        
//         const { userEmail, title, id } = row.original;

//         const emailData = {
//             to: userEmail,
//             from: session?.user?.email,
//             context: `Follow-up on the task: ${title} (ID: ${id})`,
//         };

//         console.log(emailData);

//         const response = await fetch("http://127.0.0.1:5000/api/email_sender/generate_email_ai", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json",
//             },
//             body: JSON.stringify(emailData),
//         });

//         const result = await response.json();

//         if (response.ok) {
//             console.log(result);
//             const emailDraftData = {
//                 to_recipients: userEmail,
//                 subject: result.subject,
//                 body: result.email,
//                 access_token: session?.access_token,
//             };
//             console.log(emailDraftData);
//             const response1 = await fetch("http://127.0.0.1:5000/api/email_sender/create_draft", {
//                 method: "POST",
//                 headers: {
//                     "Content-Type": "application/json",
//                 },
//                 body: JSON.stringify(emailDraftData),
//             });

//             const result1 = await response1.json();
//             console.log(result1.draft_link);
//             window.location.href = result1.draft_link;
//         } else {
//             alert(`Error: ${result.error}`);
//         }
//     } catch (error) {
//         console.error("Error sending follow-up email:", error);
//         alert("An error occurred while sending the follow-up email.");
//     }
// };

const formatDraftLink = (to: string, subject: string, body: string) => {
    
    const baseUrl = "https://outlook.office.com/mail/deeplink/compose";

    
    const encodedTo = encodeURIComponent(to);
    const encodedSubject = encodeURIComponent(subject);
    const encodedBody = encodeURIComponent(body);

    
    return `${baseUrl}?to=${encodedTo}&subject=${encodedSubject}&body=${encodedBody}`;
};

export default function DataTableDemo() {
    const [Risks, setRisks] = useState<Risk[]>([]);
    const [sorting, setSorting] = React.useState<SortingState>([])
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
        []
    )
    const [columnVisibility, setColumnVisibility] =
        React.useState<VisibilityState>({})
    const [rowSelection, setRowSelection] = React.useState({})
    const [isLoading, setIsLoading] = useState(false);
    const { data: session } = useSession();
    const isFetchedRef = useRef(false);
    const table = useReactTable({
        data: Risks,
        columns,
        onSortingChange: setSorting,
        onColumnFiltersChange: setColumnFilters,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        onColumnVisibilityChange: setColumnVisibility,
        onRowSelectionChange: setRowSelection,
        state: {
            sorting,
            columnFilters,
            columnVisibility,
            rowSelection,
        },
    })
    useEffect(() => {
        const fetchRisks = async () => {
            if (isFetchedRef.current) return; // Exit if already fetched
            isFetchedRef.current = true; //
           setIsLoading(true);

            console.log('Fetching risks...');
            try {
                const response = await fetch(flaskApiUrl('/api/risk/filter_risk_items'));
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                // API may return a JSON object { items } or a JSON-encoded string (legacy jsonify of GPT text)
                const data = await response.json();
                let parsedData: { items?: unknown[]; error?: string };
                if (typeof data === 'string') {
                    parsedData = JSON.parse(data) as { items?: unknown[] };
                } else {
                    parsedData = data as { items?: unknown[]; error?: string };
                }
                console.log('Parsed data:', parsedData);

                if (parsedData.error && !parsedData.items) {
                    console.error('Risk API error:', parsedData.error);
                }

                // Check if `parsedData` has an `items` key and ensure `items` is an array
                if (parsedData.items && Array.isArray(parsedData.items)) {
                    // console.log('Valid items array:', data.items);

                    const fetchedRisks = parsedData.items.map((item: any) => ({
                        id: item.id,
                        title: item.title,
                        state: item.state,
                        assignedTo: item.assigned_to,
                        project: item.team_project,
                        priority: item.priority,
                        severity: item.severity,
                        dueDate: item.due_date,
                        priorityScore: item.priority_score,
                        userEmail: item.user_email,
                    }));
                    //console.log(fetchedRisks);
                    setRisks(fetchedRisks);
                } else {
                    console.error('`items` is either missing or not an array:', parsedData);
                }
            } catch (error) {
                console.error('Error fetching risks:', error);
            } finally {
             setIsLoading(false); // Stop loading
            }
        };


        fetchRisks();
    }, []);




    return (
        <PageContainer>
            {isLoading && (
                <div className="loading-overlay">
                    <div className="loading-content">
                        <img src="/Loader.gif" alt="Loading..." />
                    </div>
                </div>
            )}
            <div className="w-full text-black">
                <div className="flex items-center py-4">
                    <Input
                        placeholder="Filter title..."
                        value={(table.getColumn("title")?.getFilterValue() as string) ?? ""}
                        onChange={(event) =>
                            table.getColumn("title")?.setFilterValue(event.target.value)
                        }
                        className="max-w-sm"
                    />
                    {/* <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="ml-auto">
                                Columns <ChevronDown />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            {table
                                .getAllColumns()
                                .filter((column) => column.getCanHide())
                                .map((column) => {
                                    return (
                                        <DropdownMenuCheckboxItem
                                            key={column.id}
                                            className="capitalize"
                                            checked={column.getIsVisible()}
                                            onCheckedChange={(value) =>
                                                column.toggleVisibility(!!value)
                                            }
                                        >
                                            {column.id}
                                        </DropdownMenuCheckboxItem>
                                    )
                                })}
                        </DropdownMenuContent>
                    </DropdownMenu> */}
                </div>
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            {table.getHeaderGroups().map((headerGroup) => (
                                <TableRow key={headerGroup.id}>
                                    {headerGroup.headers.map((header) => {
                                        return (
                                            <TableHead key={header.id}>
                                                {header.isPlaceholder
                                                    ? null
                                                    : flexRender(
                                                        header.column.columnDef.header,
                                                        header.getContext()
                                                    )}
                                            </TableHead>
                                        )
                                    })}
                                </TableRow>
                            ))}
                        </TableHeader>
                        <TableBody>
                            {table.getRowModel().rows?.length ? (
                                table.getRowModel().rows.map((row) => (
                                    <TableRow
                                        key={row.id}
                                        data-state={row.getIsSelected() && "selected"}
                                    >
                                        {row.getVisibleCells().map((cell) => (
                                            <TableCell key={cell.id}>
                                                {flexRender(
                                                    cell.column.columnDef.cell,
                                                    cell.getContext()
                                                )}
                                            </TableCell>
                                        ))}
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell
                                        colSpan={columns.length}
                                        className="h-24 text-center"
                                    >
                                        No results.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
                <div className="flex items-center justify-end space-x-2 py-4">
                    <div className="flex-1 text-sm text-muted-foreground">
                        {table.getFilteredSelectedRowModel().rows.length} of{" "}
                        {table.getFilteredRowModel().rows.length} row(s) selected.
                    </div>
                    <div className="space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => table.previousPage()}
                            disabled={!table.getCanPreviousPage()}
                        >
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => table.nextPage()}
                            disabled={!table.getCanNextPage()}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}
