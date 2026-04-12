'use client';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Modal } from '@/components/ui/modal';
import { Risk } from '@/constants/data';
import { MoreHorizontal } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useSession } from "next-auth/react";
import { Textarea } from '@/components/ui/textarea';
import { useEffect } from 'react';
import { toast } from 'sonner';
import { flaskApiUrl } from '@/lib/flask-api';
import Select from 'react-select'; 
interface CellActionProps {
    data: Risk;
}

export const CellAction: React.FC<CellActionProps> = ({ data }) => {
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [resultModalOpen, setResultModalOpen] = useState(false); // For showing the result modal
    const [context, setContext] = useState(""); // Store context entered by user
    const [resultData, setResultData] = useState<{ subject: string; email: string } | null>(null);
    const [emailData, setEmailData] = useState<{ [email: string]: { displayName: string; taskCount: number } } | null>(null);

    const { data: session } = useSession();
    const [emailModalOpen, setEmailModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<{ value: string; label: string }[]>([]); // Store the selected user(s)

    const userOptions = emailData
        ? Object.entries(emailData).map(([email, { displayName }]) => ({
            value: email,
            label: `${displayName} (${email})`,
    }))
    : [];
    useEffect(() => {
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
    
        fetchEmails(); // Call fetchEmails when the component mounts
    }, []);
    // Close Modal
    const closeModal = () => {
        setResultData(null); // Clear result data when modal closes
        setContext(""); // Reset context input on close
        setModalOpen(false);
        // Optionally, reset focus here

    };

    const handleSendEmailAboutTask = async () => {
        if (!selectedUser) {
            toast.error("Please select a user.");
            return;
        }
        console.log(selectedUser);
        const { title, id } = data;
        const emailData = {
            to: [selectedUser.values],
            to_name: selectedUser.map(user => user.label),
            from: session?.user?.email,
            from_name: session?.user?.name,
            context: context||`Regarding the task: ${title} (ID: ${id})`,
        };
    
        try {
            const response = await fetch(flaskApiUrl("/api/email_sender/generate_email_ai"), {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(emailData),
            });
    
            const result = await response.json();
    
            if (response.ok) {
                setResultData(result); // Display the result modal
                setResultModalOpen(true);
                setEmailModalOpen(false); // Close the dropdown modal
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error("Error sending email:", error);
            alert("An error occurred while sending the email.");
        }
    };
    

    const SendGeneratedEmail = async (session: any, userEmails: string[] | null) => {
        if (!userEmails || userEmails.length === 0) {
            userEmails = [data.userEmail];
            console.log(data.userEmail);
        }
        if (resultData ) {
            const { subject, email } = resultData;
            const emailData = {
                subject: subject,
                body: email,
                to_recipients: userEmails,
                //access_token: session?.access_token,
            };
            console.log(userEmails);

            try {
                const response = await fetch(flaskApiUrl("/api/email_sender/create_draft"), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(emailData),
                });
                const result = await response.json();
                console.log(result.draft_link);
                window.open(result.draft_link, '_blank');
                if (response.ok) {
                    toast.success("Email sent successfully.");
                } else {
                    alert("Failed to send the email.");
                }
            } catch (error) {
                console.error("Error sending generated email:", error);
                alert("An error occurred while sending the generated email.");
            }
        }
    };

    // Sending the follow-up email to the assignee
    const handleFollowUpEmail = async () => {
        try {
            const {assignedTo, userEmail, title, id } = data;
            // if (!session || !session.user) {
            // throw new Error("Session is not available.");
            // }
            
            const emailData = {
            to: userEmail,
            to_name: assignedTo,
            from: session?.user?.email,
            from_name: session?.user?.name,
            context: context || `Follow-up on the task: ${title} (ID: ${id})`,
            };
            console.log(emailData);

            const response = await fetch(flaskApiUrl("/api/email_sender/generate_email_ai"), {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(emailData),
            });

            const result = await response.json();

            if (response.ok) {
                setResultData(result);
                setResultModalOpen(true); // Open the result modal with the generated email details
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error("Error sending follow-up email:", error);
            alert("An error occurred while sending the follow-up email.");
        }
    };

    return (
        <>
            {document.body.style.pointerEvents = ''}
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuItem onClick={() => setEmailModalOpen(true)}>Send Email about task</DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setModalOpen(true)}>
                        Send Follow-up Email to assignee
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            {/* Modal for Assignee Selection */}
            <Modal isOpen={modalOpen} onClose={closeModal} title='Generate AI Email'>
                <div className="modal-header">Follow-up Email for Task</div>
                <div className="modal-body">
                    <div>
                        <div><strong>Task ID:</strong> {data.id}</div>
                        <div><strong>Title:</strong> {data.title}</div>
                        <div><strong>Assigned To:</strong> {data.assignedTo}--({data.userEmail})</div>
                        <div><strong>Sender Email:</strong> {session?.user?.email}</div>
                    </div>
                    <Textarea
                        placeholder={context || `Follow-up on the task: ${data.title} (ID: ${data.id})`}
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        rows={4}
                    />
                </div>
                <div className="modal-footer m-4">

                    <Button className="mx-3" variant="outline" onClick={closeModal}>
                        Cancel
                    </Button>
                    <Button className='mx-3' onClick={handleFollowUpEmail} >
                        Generate Email
                    </Button>
                </div>
            </Modal>

            {/* Result Modal to show the response */}
            <Modal isOpen={resultModalOpen} onClose={() => setResultModalOpen(false)} title="Email Preview">
                <div className="modal-body">
                    <div><strong>Subject:</strong> {resultData?.subject}</div>
                    <div><strong>Email Body:</strong></div>
                    <div
                        dangerouslySetInnerHTML={{
                            __html: resultData?.email?.replace(/\n/g, "<br />") || ""
                        }}
                    />
                </div>
                <div className="modal-footer mt-2">
                    
                    <Button className='mx-2' variant="outline" onClick={() => setResultModalOpen(false)}>
                        Close
                    </Button>
                    <Button className='mx-1' onClick={() => SendGeneratedEmail(session, selectedUser.map(user => user.value))}>
                        Send Emails
                    </Button>
                </div>
            </Modal>

            <Modal isOpen={emailModalOpen} onClose={() => setEmailModalOpen(false)} title="Send Email About Task">
    <div className="modal-body">
        <div>
            <div><strong>Task ID:</strong> {data.id}</div>
            <div><strong>Title:</strong> {data.title}</div>
            <div><strong>Sender Email:</strong> {session?.user?.email}</div>
            <div className="mt-4">
                <label className="font-medium">Select Users:</label>
                <Select
                    isMulti
                    options={userOptions}
                    value={selectedUser.length === 0 && data.userEmail ? [{ value: data.userEmail, label: `${data.assignedTo} (${data.userEmail})` }] : selectedUser}
                    onChange={(selectedOptions) => setSelectedUser(selectedOptions as { value: string; label: string }[])}
                    placeholder="Select users..."
                />
            </div>
            <label className="font-medium">Select Context:</label>
            <Textarea
                        className='mt-4'
                        placeholder={context || `Follow-up on the task: ${data.title} (ID: ${data.id})`}
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        rows={4}
                    />
        </div>
    </div>
    <div className="modal-footer m-4">
        <Button variant="outline" onClick={() => setEmailModalOpen(false)}>
            Cancel
        </Button>
        <Button
            className="ml-3"
            onClick={handleSendEmailAboutTask}
            disabled={!selectedUser}
        >
            Generate Email
        </Button>
    </div>
</Modal>
        </>
    );
};
