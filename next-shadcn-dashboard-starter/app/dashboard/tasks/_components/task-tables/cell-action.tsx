'use client';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Modal } from '@/components/ui/modal'; // Assume you have a reusable Modal component
import { Task } from '@/constants/data';
import { AppWindow, MoreHorizontal, Edit } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { toast } from 'sonner';
import { flaskApiUrl } from '@/lib/flask-api';

interface CellActionProps {
  data: Task;
}

export const CellAction: React.FC<CellActionProps> = ({ data }) => {
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [emailData, setEmailData] = useState<{ [email: string]: { displayName: string; taskCount: number } } | null>(null);
  const router = useRouter();

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const response = await fetch(flaskApiUrl('/api/automated_task_assignment/task_counts'));
      const data = await response.json();
      setEmailData(data);
    } catch (error) {
      console.error('Error fetching email data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignManually = () => {
    if (!emailData) {
      fetchEmails();
    }
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
  };

  const assignTask = async (email: string) => {
    try {
      const url = flaskApiUrl(`/api/automated_task_assignment/update_work_item/${data.id}/${encodeURIComponent(email)}`);
      const response = await fetch(url, {
        method: 'POST',
        mode: 'cors',
      });

      if (response.ok) {
        toast.success(`Task successfully assigned to ${email}`);
        console.log(`Task assigned to ${email}`);
        closeModal(); // Close the modal after successful assignment
      } else {
        console.error('Failed to assign task');
      }
    } catch (error) {
      console.error('Error assigning task:', error);
    }
  };

  return (
    <>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Actions</DropdownMenuLabel>

          {/* <DropdownMenuItem onClick={() => router.push(`/dashboard/user/${data.id}`)}>
            <AppWindow className="mr-2 h-4 w-4" />
            Go To DevOps
          </DropdownMenuItem> */}

          <DropdownMenuItem onClick={handleAssignManually}>
            <Edit className="mr-2 h-4 w-4" /> Assign manually
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Modal for Assignee Selection */}
      {modalOpen && (
        <Modal isOpen={modalOpen} onClose={closeModal} title="Assign Task Manually" description="Select an assignee for the task.">
          <div className="p-4">
            <div className="font-semibold text-sm mb-2">Select Assignee</div>
            {loading ? (
              <div className="text-center text-gray-500">Loading...</div>
            ) : (
              emailData &&
              Object.entries(emailData).map(([email, details]) => (
                <div
                  key={email}
                  className="p-2 hover:bg-gray-100 cursor-pointer"
                  onClick={() => assignTask(email)} // Trigger the POST request on click
                >
                  {details.displayName} ({details.taskCount} tasks)
                </div>
              ))
            )}
          </div>
        </Modal>
      )}
    </>
  );
};
