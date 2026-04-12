'use client';

import React, { useEffect, useState } from 'react';
import { flaskApiUrl } from '@/lib/flask-api';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export function RecentSales() {
  const [taskData, setTaskData] = useState<any>(null);

  useEffect(() => {
    // Fetch data from the API
    const fetchData = async () => {
      const response = await fetch(
        flaskApiUrl('/api/automated_task_assignment/task_counts')
      );
      const data = await response.json();
      setTaskData(data);
    };

    fetchData();
  }, []);

  // If the data is not yet loaded, you can return a loading state
  if (!taskData) {
    return (
      <div
        className="flex h-full items-center justify-center"
        style={{ margin: '20%' }}
      >
        <img
          className="mx-auto"
          height={100}
          width={100}
          src="/Loader.gif"
          alt="Loader"
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {Object.keys(taskData).map((email) => {
        const { displayName, taskCount } = taskData[email];

        return (
          <div className="flex items-center" key={email}>
            <Avatar className="h-9 w-9">
              <AvatarImage src="/avatars/01.png" alt="Avatar" />
              <AvatarFallback>
                {displayName?.slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="ml-4 space-y-1">
              <p className="text-sm font-medium leading-none">{displayName}</p>
              <p className="text-sm text-muted-foreground">{email}</p>
            </div>
            <div className="ml-auto font-medium">
              Working on {taskCount} tasks
            </div>
          </div>
        );
      })}
    </div>
  );
}
