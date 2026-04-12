'use client';
import { AreaGraph } from './area-graph';
import { BarGraph } from './bar-graph';
import { PieGraph } from './pie-graph';
import { CalendarDateRangePicker } from '@/components/date-range-picker';
import PageContainer from '@/components/layout/page-container';
import { RecentSales } from './recent-sales';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useSession } from 'next-auth/react';
import Select from 'react-select';
import { Modal } from '@/components/ui/modal';
import { flaskApiUrl } from '@/lib/flask-api';
export default function OverViewPage() {
  const [taskData, setTaskData] = useState<any>(null);
  const [emailData, setEmailData] = useState<any[]>([]); // Store email data
  const [selectedUser, setSelectedUser] = useState<any | null>(null); // Store selected user
  const [isModalOpen, setIsModalOpen] = useState(false); // Track modal state
  const [loading, setLoading] = useState(false);
  const { data: session } = useSession(); // Getting the session token
  const [projects, setProjects] = useState<any[]>([]); // Store projects data
        const [selectedProject, setSelectedProject] = useState<any | null>(null); // Store selected project
        const [isReportReady, setIsReportReady] = useState(false);
        const fetchEmails = async () => {
          try {
            setLoading(true);
            const response = await fetch(flaskApiUrl('/api/automated_task_assignment/task_counts'));
            const data = await response.json();
            const emailArray = Object.keys(data).map(key => ({
              email: key,
              displayName: data[key].displayName,
              taskCount: data[key].taskCount,
            }));
            setEmailData(emailArray);
          } catch (error) {
            console.error('Error fetching email data:', error);
          } finally {
            setLoading(false);
          }
        };
        const fetchData = async () => {
          const response = await fetch(
            flaskApiUrl('/api/stats/count_work_items_by_type')
          );
          const data = await response.json();
          setTaskData(data);
        };
        const fetchCurrentProject = async () => {
          try {
            const response = await fetch(flaskApiUrl('/api/get_current_project'));
            const data = await response.json();
            setSelectedProject(data.name);
            if(response.ok) {
              console.log('Current project:', data);
            }
          } catch (error) {
            console.error('Error fetching current project:', error);
          }
        };

        useEffect(() => {
          fetchCurrentProject();
          fetchEmails();
          fetchData();
        }, []);
        useEffect(() => {
          const fetchProjects = async () => {
            try {
              const response = await fetch(flaskApiUrl('/api/get_projects'));
              const data = await response.json();
              setProjects(data);
            } catch (error) {
              console.error('Error fetching projects:', error);
            }
          };
          fetchProjects();
        }, []);
  // useEffect(() => {
  //   const fetchEmails = async () => {
  //     try {
  //       setLoading(true);
  //       const response = await fetch('http://127.0.0.1:5000/api/automated_task_assignment/task_counts');
  //       const data = await response.json();
  //       const emailArray = Object.keys(data).map(key => ({
  //         email: key,
  //         displayName: data[key].displayName,
  //         taskCount: data[key].taskCount,
  //       }));

        
        
  //       setEmailData(emailArray);
  //     } catch (error) {
  //       console.error('Error fetching email data:', error);
  //     } finally {
  //       setLoading(false);
  //     }
  //   };
  //   fetchEmails(); 
  // }, []);


  // useEffect(() => {
  //   // Fetch data from the API
  //   const fetchData = async () => {
  //     const response = await fetch(
  //       'http://127.0.0.1:5000/api/stats/count_work_items_by_type'
  //     );
  //     const data = await response.json();
  //     setTaskData(data);
  //   };

  //   fetchData();
  // }, []);

  const generateStatusReport = async (session: any) => {
    try {
      setIsReportReady(false);
      // Request to generate the report
      const response = await fetch(flaskApiUrl('/api/status/generate_status_report_plan'), {
        method: 'GET',
      });

      if (response.ok) {
        setIsReportReady(true);
        // Extract the file name from the Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const fileName = contentDisposition
          ? contentDisposition.split('filename=')[1].replace(/"/g, '') // Extract file name
          : 'work_items_due_dates.xlsx';

        // Convert response to Blob and create a download link
        
      } else {
        console.error('Failed to generate the report:', await response.text());
      }
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };
  

  const modalContent = (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Select User</label>
        <Select
          options={emailData.map((user) => ({
            label: user.displayName,
            value: user.email,
          }))}
          value={selectedUser}
          onChange={setSelectedUser}
          getOptionLabel={(e: any) => `${e.label} (${e.value})`} // Display email with name
          placeholder="Select a user"
        />
      </div>
      <div className="flex justify-end space-x-2">
        <Button onClick={() => setIsModalOpen(false)}>Cancel</Button>
        <Button onClick={() => generateStatusReport(session)} disabled={!selectedUser}>
          OK
        </Button>
      </div>
    </div>
  );


  if (!taskData) {
    // Render a loading state while data is being fetched
    return <div>Loading...</div>;
  }
  return (
    <PageContainer scrollable>
      <div className="space-y-2">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-black">
            Hi, Welcome back 👋  
            <p className='text-base'>{selectedProject ? `Current Project: ${selectedProject}` : 'No project selected'}</p>
          </h2>
          
         
        


            <div className="flex items-center space-x-2">
            <Select
              options={Array.isArray(projects) ? projects.map((project) => ({
              label: project.name,
              value: project.id,
              })) : []}
              value={selectedProject}
              onChange={(selectedOption) => {
              setSelectedProject(selectedOption);
              fetch(flaskApiUrl('/api/switch_project'), {
                method: 'POST',
                mode: 'cors',
                headers: {
                'Content-Type': 'application/json',
                },
                body: JSON.stringify({ project: selectedOption.label }),
              })
                .then((response) => response.json())
                .then((data) => {
                console.log('Project switched:', data);
                fetchCurrentProject();
                window.location.reload(); // Refresh the page
                })
                .catch((error) => {
                console.error('Error switching project:', error);
                });
              }}
              placeholder="Select a project"
              className="text-black"
            />
            <Button onClick={() =>generateStatusReport(session)}>Generate Daily Report</Button>
            {isReportReady && (
                <a href={flaskApiUrl('/download-report')} download className="download-button">
                    <Button variant="link" className='text-black'>Download Report</Button>
                </a>
            )}
            {isModalOpen && (
              <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Generate Report">
              {modalContent}
              </Modal>
            )}
            </div>
        
        </div>
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            {/* <TabsTrigger value="analytics" disabled>
              Analytics
            </TabsTrigger> */}
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Pending Tasks
                  </CardTitle>
                  <svg
                    className="text-black"
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
                    <path d="M14 2v4a2 2 0 0 0 2 2h4" />
                    <path d="m9 15 2 2 4-4" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {taskData['Task'] || 0}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Feature</CardTitle>
                  <svg
                    className="text-black"
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M6 3h12l4 6-10 13L2 9Z" />
                    <path d="M11 3 8 9l4 13 4-13-3-6" />
                    <path d="M2 9h20" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {taskData['Feature'] || 0}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Pending Bug Fixes
                  </CardTitle>
                  <svg
                    className="text-black"
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="m8 2 1.88 1.88" />
                    <path d="M14.12 3.88 16 2" />
                    <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" />
                    <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6" />
                    <path d="M12 20v-9" />
                    <path d="M6.53 9C4.6 8.8 3 7.1 3 5" />
                    <path d="M6 13H2" />
                    <path d="M3 21c0-2.1 1.7-3.9 3.8-4" />
                    <path d="M20.97 5c0 2.1-1.6 3.8-3.5 4" />
                    <path d="M22 13h-4" />
                    <path d="M17.2 17c2.1.1 3.8 1.9 3.8 4" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {taskData['Bug'] || 0}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Epics</CardTitle>
                  <svg
                    className="text-black"
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M11.562 3.266a.5.5 0 0 1 .876 0L15.39 8.87a1 1 0 0 0 1.516.294L21.183 5.5a.5.5 0 0 1 .798.519l-2.834 10.246a1 1 0 0 1-.956.734H5.81a1 1 0 0 1-.957-.734L2.02 6.02a.5.5 0 0 1 .798-.519l4.276 3.664a1 1 0 0 0 1.516-.294z" />
                    <path d="M5 21h14" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {taskData['Epic'] || 0}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Product Backlog Items
                  </CardTitle>
                  <svg
                    className="text-black"
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M3 12h.01" />
                    <path d="M3 18h.01" />
                    <path d="M3 6h.01" />
                    <path d="M8 12h13" />
                    <path d="M8 18h13" />
                    <path d="M8 6h13" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {taskData['Product Backlog Item'] || 0}
                  </div>
                </CardContent>
              </Card>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-7">
              <div className="col-span-4">
                <BarGraph />
              </div>
              <Card className="col-span-4 md:col-span-3">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    {/* Title Section */}
                    <div>
                      <CardTitle>Active Users</CardTitle>
                      <CardDescription></CardDescription>
                    </div>
                    {/* Button Section */}
                    <div className="hidden items-center space-x-2 md:flex">
                      {/* <CalendarDateRangePicker /> */}
                      {/* <Button>Get AI</Button> */}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <RecentSales />
                </CardContent>
              </Card>

              <div className="col-span-4">
                <AreaGraph />
              </div>
              <div className="col-span-4 md:col-span-3">
                <PieGraph />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PageContainer>
  );
}
