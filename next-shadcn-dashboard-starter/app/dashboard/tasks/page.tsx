"use client"
import { CellAction } from './_components/task-tables/cell-action';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import PageContainer from "@/components/layout/page-container"
import { Task } from "@/constants/data"
import { useEffect, useState } from "react"
import { toast } from 'sonner';
import { Modal } from '@/components/ui/modal';
import { DialogContent, DialogTitle } from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { flaskApiUrl } from '@/lib/flask-api';



export const columns: ColumnDef<Task>[] = [
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
  // {
  //   accessorKey: "ID",
  //   header: "id",
  //   cell: ({ row }) => row.getValue("id")
  // },
  {
    accessorKey: "id",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          ID
          <ArrowUpDown />
        </Button>
      )
    },
    cell: ({ row }) => <div className="lowercase">{row.getValue("id")}</div>,
  },
  {
    accessorKey: "title",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Title
          <ArrowUpDown />
        </Button>
      )
    },
    cell: ({ row }) => <div className="lowercase">{row.getValue("title")}</div>,
  },
  {
    accessorKey: "workItemType",
    header: "Type",
    cell: ({ row }) => row.getValue("workItemType")
  },
  {
    accessorKey: "state",
    header: "State",
    cell: ({ row }) => row.getValue("state")
  },
  {
    id: 'actions',
    cell: ({ row }) => <CellAction data={row.original} />
  }
  
  
]

export default function DataTableDemo() {

  const [tasks, setTasks] = useState<Task[]>([]);
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  )
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})
  const [idsArray, setIdsArray] = useState([]);
  const [responseData, setResponseData] = useState<{ [key: string]: string }[] | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const handleButtonClick = async () => {
    const filteredRows = table.getFilteredSelectedRowModel().rows;

    if (filteredRows.length > 0) {
      setIsLoading(true); // Start loading
      const taskIds = filteredRows.map((row) => row.original.id);

      try {
        const response = await fetch(
          flaskApiUrl('/api/status_report/generate_gpt_task_assignment'),
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ task_ids: taskIds }),
          }
        );

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        setResponseData(data);
        setIsModalOpen(true);
        toast.success('Task assignment generated successfully!');
      } catch (error) {
        toast.error('Error generating task assignments');
        console.error('Error:', error);
      } finally {
        setIsLoading(false); // Stop loading
      }
    } else {
      toast.error('Please select at least one item to assign.');
    }
  };

  useEffect(() => {
    const fetchTasks = async () => {
      setIsLoading(true); // Start loading
      try {
        const response = await fetch(
          flaskApiUrl('/api/automated_task_assignment/fetch_unassigned_tasks')
        );
        const data = await response.json();

        const fetchedTasks = data.workItems.map((item: any) => ({
          id: item.id,
          url: item.url,
          workItemType: item.fields['System.WorkItemType'],
          state: item.fields['System.State'],
          title: item.fields['System.Title'],
        }));

        setTasks(fetchedTasks);
      } catch (error) {
        console.error('Error fetching tasks:', error);
      } finally {
        setIsLoading(false); // Stop loading
      }
    };

    fetchTasks();
  }, []);

  const assignTask = async (taskId: string, email: string) => {
    setIsLoading(true); // Start loading
    try {
      const url = flaskApiUrl(`/api/automated_task_assignment/update_work_item/${taskId}/${encodeURIComponent(email)}`);
      const response = await fetch(url, {
        method: 'POST',
        mode: 'cors',
      });

      if (response.ok) {
        toast.success(`Task successfully assigned to ${email}`);
        setResponseData((prevData) =>
          prevData ? prevData.filter((task) => !task.hasOwnProperty(taskId)) : []
        );
      } else {
        throw new Error('Failed to assign task');
      }
    } catch (error) {
      toast.error(`Error assigning task: ${(error as Error).message}`);
      console.error('Error:', error);
    } finally {
      setIsLoading(false); // Stop loading
    }
  };

  const assignAllTasks = async () => {
    if (!responseData || responseData.length === 0) return;

    setIsLoading(true); // Start loading
    try {
      const tasksToAssign = responseData.map((task: { [key: string]: string }) => {
        const taskId = Object.keys(task)[0];
        const taskAssignments = JSON.parse(task[taskId]).assignments;
        const email = taskAssignments[0]?.email;

        return { taskId, email };
      });

      const response = await fetch(
        flaskApiUrl('/api/automated_task_assignment/bulk_update'),
        {
          method: 'POST',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(tasksToAssign),
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success('All tasks successfully assigned');
        setResponseData([]);
        console.log('Bulk assignment result:', result);
      } else {
        throw new Error('Failed to assign tasks in bulk');
      }
    } catch (error) {
      toast.error('Error assigning all tasks');
      console.error('Error:', error);
    } finally {
      setIsLoading(false); // Stop loading
    }
  };
  const removeTask = async (taskId: string) => {
    try {
      setResponseData((prevData) =>
      prevData ? prevData.filter((task) => !task.hasOwnProperty(taskId)) : []
      );
    } catch (error) {
      toast.error(`Error removing task: ${String(error)}`);
    }
  }
  const table = useReactTable({
    data:tasks,
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
      <div className="flex items-around justify-between py-4">
        <Input
          placeholder="Search Tasks..."
          value={(table.getColumn("title")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("title")?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
        <div>
        {/* <DropdownMenu >
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
        <Button  className="mx-2 ml-auto" onClick={handleButtonClick}>
              Ask AI to assign 
        </Button>
        </div>
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
    <div>
      {/* {table.getFilteredSelectedRowModel().rows.map((row) => (
        // <div className='text-black' key={row.id}>{row.original.id}</div>
        
      ))} */}
    </div>
    
    <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={''}>
      <div>
        <h1>Task Assignments</h1>
        
        {responseData && responseData.length > 0 ? (
          <div className="mt-4 text-black mx-auto p-6">
            <table>
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>User Email</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {responseData.map((task: { [key: string]: string }, index: number) => {
                  const taskId = Object.keys(task)[0];
                  const taskAssignments = JSON.parse(task[taskId]).assignments;
    
                    return (
                    <tr key={index}>
                       <td className='p-2'>{taskId}</td>
                      <td className='p-2'>{taskAssignments[0]?.email}</td>
                      <td className='p-2'>{taskAssignments[0]?.reason}</td>
                      <td className='p-2'>
                      <Button onClick={() => assignTask(taskId, taskAssignments[0]?.email)}>
                        <div className='p-2 text-nowrap'>Confirm AI suggestions</div>
                      </Button>
                      </td>
                      <td className='p-2'>
                      <X role='button' onClick={() => removeTask(taskId)} />
                      </td>
                      <td className='p-2'>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                        <Button variant="outline">Options</Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                        {taskAssignments.map((assignment: any, idx: number) => (
                          <DropdownMenuItem
                            key={idx}
                            onClick={() => {
                              const updatedResponseData = responseData.map((task, taskIndex) => {
                                if (taskIndex === index) {
                                  const currentAssignments = JSON.parse(task[taskId]).assignments;
                                  return {
                                    [taskId]: JSON.stringify({
                                      assignments: [assignment, ...currentAssignments.filter((a: any) => a.email !== assignment.email)],
                                    }),
                                  };
                                }
                                return task;
                              });
                              setResponseData(updatedResponseData);
                            }}
                          >
                            {assignment.email} - {assignment.reason}
                          </DropdownMenuItem>
                        ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                      </td>
                    </tr>
                    );
                  })}
                  </tbody>
                  </table>
                </div>
                ) : (
                <div className='p-2 w-full text-center'>No tasks left</div>
                )}
        <Button
          className="p-2 mx-2"
          onClick={() => assignAllTasks()}
        >
          Assign All Tasks
        </Button>
    
        <Button className='mx-2' variant={'outline'} onClick={() => setIsModalOpen(false)}>Close</Button>
      </div>
    </Modal>
      


    </PageContainer>
  )
  // const idsArray = table.getFilteredSelectedRowModel().rows.map((row) => row.original.id);
}
// {
  //   accessorKey: "amount",
  //   header: () => <div className="text-right">Amount</div>,
  //   cell: ({ row }) => {
  //     const amount = parseFloat(row.getValue("amount"))

  //     // Format the amount as a dollar amount
  //     const formatted = new Intl.NumberFormat("en-US", {
  //       style: "currency",
  //       currency: "USD",
  //     }).format(amount)

  //     return <div className="text-right font-medium">{formatted}</div>
  //   },
  // },
  
  // {
  //   id: "actions",
  //   enableHiding: false,
  //   cell: ({ row }) => {
  //     const payment = row.original

  //     return (
  //       <DropdownMenu>
  //         <DropdownMenuTrigger asChild>
  //           <Button variant="ghost" className="h-8 w-8 p-0">
  //             <span className="sr-only">Open menu</span>
  //             <MoreHorizontal />
  //           </Button>
  //         </DropdownMenuTrigger>
  //         <DropdownMenuContent align="end">
  //           <DropdownMenuLabel>Actions</DropdownMenuLabel>
  //           <DropdownMenuItem
  //             onClick={() => navigator.clipboard.writeText(payment.id)}
  //           >
  //             Copy payment ID
  //           </DropdownMenuItem>
  //           <DropdownMenuSeparator />
  //           <DropdownMenuItem>View customer</DropdownMenuItem>
  //           <DropdownMenuItem>View payment details</DropdownMenuItem>
  //         </DropdownMenuContent>
  //       </DropdownMenu>
  //     )
  //   },
  // },