'use client';

import * as React from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  department: string;
  sentiment: number;
}

const mockData: Course[] = [
  {
    id: '1',
    code: 'CS 101',
    name: 'Introduction to Computer Science',
    credits: 3,
    department: 'Computer Science',
    sentiment: 4.5,
  },
  {
    id: '2',
    code: 'CS 201',
    name: 'Data Structures and Algorithms',
    credits: 4,
    department: 'Computer Science',
    sentiment: 4.2,
  },
  {
    id: '3',
    code: 'MATH 141',
    name: 'Calculus I',
    credits: 4,
    department: 'Mathematics',
    sentiment: 3.8,
  },
  {
    id: '4',
    code: 'ENGL 104',
    name: 'Academic Writing',
    credits: 3,
    department: 'English',
    sentiment: 4.0,
  },
  {
    id: '5',
    code: 'CS 350',
    name: 'Operating Systems',
    credits: 3,
    department: 'Computer Science',
    sentiment: 3.9,
  },
];

const columns: ColumnDef<Course>[] = [
  {
    accessorKey: 'code',
    header: 'Code',
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue('code')}</div>
    ),
  },
  {
    accessorKey: 'name',
    header: 'Course Name',
    cell: ({ row }) => <div>{row.getValue('name')}</div>,
  },
  {
    accessorKey: 'department',
    header: 'Department',
    cell: ({ row }) => <div>{row.getValue('department')}</div>,
  },
  {
    accessorKey: 'credits',
    header: 'Credits',
    cell: ({ row }) => <div className="text-center">{row.getValue('credits')}</div>,
  },
  {
    accessorKey: 'sentiment',
    header: 'Rating',
    cell: ({ row }) => {
      const sentiment = parseFloat(row.getValue('sentiment'));
      return (
        <div className="flex items-center">
          <span className="font-medium">{sentiment.toFixed(1)}</span>
          <span className="ml-1 text-muted-foreground">/ 5.0</span>
        </div>
      );
    },
  },
];

export function CourseTable() {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);

  const table = useReactTable({
    data: mockData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() && 'selected'}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
