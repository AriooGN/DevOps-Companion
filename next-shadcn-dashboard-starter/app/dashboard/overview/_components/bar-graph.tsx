'use client';

import * as React from 'react';
import {
  Bar, BarChart, CartesianGrid, XAxis, YAxis, Legend, Tooltip
} from 'recharts';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card';
import {
  ChartContainer, ChartTooltipContent
} from '@/components/ui/chart';
import { flaskApiUrl } from '@/lib/flask-api';

export const description = 'An interactive bar chart';

const chartConfig = {
  Done: {
    label: 'Done',
    color: 'hsl(var(--chart-1))'
  },
  InProgress: {
    label: 'In Progress',
    color: 'hsl(var(--chart-2))'
  },
  New: {
    label: 'New',
    color: 'hsl(var(--chart-3))'
  }
};

export function BarGraph() {
  interface ChartData {
    Done: number;
    'In Progress': number;
    New: number;
  }

  const [chartData, setChartData] = React.useState<ChartData[]>([]);

  React.useEffect(() => {
    async function fetchChartData() {
      try {
        const response = await fetch(flaskApiUrl('/api/stats/count_work_items_by_state'));
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        setChartData([data]); // Wrap in array to match Recharts data structure
      } catch (error) {
        console.error('Error fetching chart data:', error);
      }
    }

    fetchChartData();
  }, []); // Empty dependency array ensures this runs once on mount

  const total = React.useMemo(
    () => ({
      Done: chartData.reduce((acc, curr) => acc + (curr.Done || 0), 0),
      InProgress: chartData.reduce((acc, curr) => acc + (curr['In Progress'] || 0), 0),
      New: chartData.reduce((acc, curr) => acc + (curr.New || 0), 0)
    }),
    [chartData]
  );

  return (
    <Card>
      <CardHeader className="flex flex-col items-stretch space-y-0 border-b p-0 sm:flex-row">
        <div className="flex flex-1 flex-col justify-center gap-1 px-6 py-5 sm:py-6">
          <CardTitle>Bar Graph for Work items in different states</CardTitle>
          <CardDescription>
            Showing counts for different statuses (Done, In Progress, New)
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="px-2 sm:p-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[280px] w-full"
        >
          <BarChart
            data={chartData}
            margin={{
              left: 12,
              right: 12
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis dataKey="States" tickLine={false} axisLine={false} tickMargin={8} minTickGap={32} />
            <YAxis />
            <Legend />
            <Tooltip content={<ChartTooltipContent />} />
            <Bar dataKey="Done" fill={`var(--color-Done)`} />
            <Bar dataKey="New" fill={`var(--color-New)`} />
            <Bar dataKey="In Progress" fill={`var(--color-InProgress)`} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
