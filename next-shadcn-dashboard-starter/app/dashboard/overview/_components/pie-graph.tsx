'use client';

import * as React from 'react';
import { TrendingUp } from 'lucide-react';
import { Label, Pie, PieChart } from 'recharts';
import { useEffect, useState } from 'react';

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

// Initial empty data for the chart
const initialChartData = [
  { name: 'Assigned Tasks', value: 0, fill: 'var(--color-assigned)' },
  { name: 'Unassigned Tasks', value: 0, fill: 'var(--color-unassigned)' },
];

const chartConfig = {
  tasks: {
    label: 'Task Assignment'
  },
  assigned: {
    label: 'Assigned Tasks',
    color: 'hsl(var(--chart-2))'
  },
  unassigned: {
    label: 'Unassigned Tasks',
    color: 'hsl(var(--chart-5))'
  }
} satisfies ChartConfig;

export function PieGraph() {
  const [chartData, setChartData] = useState(initialChartData);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(flaskApiUrl('/api/stats/count_work_items_by_assignment'));
        const data = await response.json();
        // Assuming API response has { assigned: number, unassigned: number }
        setChartData([
          { name: 'Assigned Tasks: ', value: data.assigned, fill: 'var(--color-assigned)' },
          { name: 'Unassigned Tasks: ', value: data.unassigned, fill: 'var(--color-unassigned)' },
        ]);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  const totalTasks = React.useMemo(() => {
    return chartData.reduce((acc, curr) => acc + curr.value, 0);
  }, [chartData]);

  return (
    <Card className="flex flex-col">
      <CardHeader className="items-center pb-0">
        <CardTitle>Pie Chart for assigned and  unassigned work items</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <ChartContainer
          config={chartConfig}
          className="mx-auto aspect-square max-h-[360px]"
        >
          <PieChart>
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent hideLabel />}
            />
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={60}
              strokeWidth={5}
            >
              <Label
                content={({ viewBox }) => {
                  if (viewBox && 'cx' in viewBox && 'cy' in viewBox) {
                    return (
                      <text
                        x={viewBox.cx}
                        y={viewBox.cy}
                        textAnchor="middle"
                        dominantBaseline="middle"
                      >
                        <tspan
                          x={viewBox.cx}
                          y={viewBox.cy}
                          className="fill-foreground text-3xl font-bold"
                        >
                          {totalTasks.toLocaleString()}
                        </tspan>
                        <tspan
                          x={viewBox.cx}
                          y={(viewBox.cy || 0) + 24}
                          className="fill-muted-foreground"
                        >
                          Tasks
                        </tspan>
                      </text>
                    );
                  }
                }}
              />
            </Pie>
          </PieChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex-col gap-2 text-sm">
        <div className="flex items-center gap-2 font-medium leading-none">
         
        </div>
        <div className="leading-none text-muted-foreground">
          Showing current task assignments split by assigned and unassigned tasks
        </div>
      </CardFooter>
    </Card>
  );
}
