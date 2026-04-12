'use client';

import { useEffect, useState } from 'react';
import { TrendingUp } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, XAxis } from 'recharts';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent
} from '@/components/ui/chart';
import { flaskApiUrl } from '@/lib/flask-api';

const chartConfig = {
  Epic: {
    label: 'Epic',
    color: 'hsl(var(--chart-2))'
  },
  Bug: {
    label: 'Bug',
    color: 'hsl(var(--chart-1))'
  },
  Feature: {
    label: 'Feature',
    color: 'hsl(var(--chart-3))'
  },
  'Product Backlog Item': {
    label: 'Product Backlog Item',
    color: 'hsl(var(--chart-4))'
  },
  Task: {
    label: 'Task',
    color: 'hsl(var(--chart-5))'
  }
} satisfies ChartConfig;

export function AreaGraph() {
  const [chartData, setChartData] = useState<{ type: string; count: number }[]>([]);

  useEffect(() => {
    async function fetchChartData() {
      try {
        const response = await fetch(flaskApiUrl('/api/stats/count_work_items_by_type'));
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const data = await response.json();

        // Transform the API response into the format expected by Recharts
        const transformedData = Object.entries(data).map(([type, count]) => ({
          type,
          count: count as number
        }));

        setChartData(transformedData);
      } catch (error) {
        console.error('Error fetching chart data:', error);
      }
    }

    fetchChartData();
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Area Chart</CardTitle>
        <CardDescription>
          Showing distribution of work items by type
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[310px] w-full"
        >
          <AreaChart
            data={chartData}
            margin={{
              left: 12,
              right: 12
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="type"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="dot" />}
            />
            <Area
              dataKey="count"
              type="natural"
              fill="var(--color-Bug)"
              fillOpacity={0.4}
              stroke="var(--color-Bug)"
              stackId="a"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
      <CardFooter>
        <div className="flex w-full items-start gap-2 text-sm">
          <div className="grid gap-2">
            <div className="flex items-center gap-2 font-medium leading-none">
             
            </div>
            <div className="flex items-center gap-2 leading-none text-muted-foreground">
              Distribution of work items by their types
            </div>
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
