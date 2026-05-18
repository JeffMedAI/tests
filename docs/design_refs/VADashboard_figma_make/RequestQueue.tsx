import { useState } from 'react';
import { Clock, AlertTriangle, User, Calendar, Phone, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { Card } from './ui/card';

export interface Request {
  id: string;
  patientName: string;
  dob: string;
  nhsNumber: string;
  requestType: 'Prescription' | 'Sick Note' | 'Referral' | 'Admin' | 'Test Result' | 'Appointment';
  priority: 'Urgent' | 'High' | 'Normal' | 'Low';
  summary: string;
  timeReceived: string;
  ageMinutes: number;
  assignedTo?: string;
  status: 'Unassigned' | 'In Progress' | 'Resolved' | 'Overdue';
  hasRedFlag?: boolean;
  phone: string;
  postcode: string;
  detailedInfo?: {
    triageNotes?: string[];
    conversation?: Array<{ speaker: string; text: string }>;
    duration?: string;
  };
}

const mockRequests: Request[] = [
  {
    id: '1',
    patientName: 'Emily Thompson',
    dob: '15/03/1978',
    nhsNumber: '485 762 1234',
    requestType: 'Appointment',
    priority: 'Urgent',
    summary: 'Severe chest pain radiating to left arm, started 30 minutes ago. Patient reports difficulty breathing and feeling dizzy.',
    timeReceived: '14:32',
    ageMinutes: 8,
    status: 'Unassigned',
    hasRedFlag: true,
    phone: '+447821456789',
    postcode: 'L22 4TG',
    detailedInfo: {
      duration: '3:45',
      triageNotes: [
        'When did the chest pain start? About 30 minutes ago.',
        'Does the pain radiate anywhere? Yes, down my left arm.',
        'Are you experiencing shortness of breath? Yes, finding it hard to breathe.',
        'Any dizziness or nausea? Feeling very dizzy and a bit nauseous.',
        'Do you have a history of heart problems? My father had a heart attack at 55.'
      ],
      conversation: [
        { speaker: 'VA', text: 'Hello, this is the Virtual Assistant for Churchtown Medical Centre. Are you calling about yourself?' },
        { speaker: 'Caller', text: 'Yes, I need help urgently.' },
        { speaker: 'VA', text: 'What is the emergency?' },
        { speaker: 'Caller', text: 'I have severe chest pain and it\'s going down my left arm.' }
      ]
    }
  },
  {
    id: '2',
    patientName: 'James Harrison',
    dob: '22/09/1985',
    nhsNumber: '456 123 9876',
    requestType: 'Prescription',
    priority: 'Normal',
    summary: 'Repeat prescription request for Metformin 500mg and Atorvastatin 20mg. Current supply runs out in 3 days. Prefers Boots Pharmacy.',
    timeReceived: '14:15',
    ageMinutes: 25,
    assignedTo: 'Prescribing Team',
    status: 'In Progress',
    phone: '+447912345678',
    postcode: 'L25 3PD',
    detailedInfo: {
      duration: '2:15',
      triageNotes: [
        'Which medications? Metformin 500mg and Atorvastatin 20mg.',
        'How long will current supply last? About 3 days.',
        'Any side effects? None, working well.',
        'Preferred pharmacy? Boots Pharmacy on High Street.'
      ]
    }
  },
  {
    id: '3',
    patientName: 'Sarah Mitchell',
    dob: '10/11/1992',
    nhsNumber: '398 456 7123',
    requestType: 'Sick Note',
    priority: 'High',
    summary: 'Extension needed for existing sick note. Recovering from anxiety and depression, currently off work for 2 weeks. Therapist recommends additional 4 weeks.',
    timeReceived: '13:58',
    ageMinutes: 42,
    status: 'Overdue',
    hasRedFlag: true,
    phone: '+447654321987',
    postcode: 'L18 6HQ',
    detailedInfo: {
      duration: '4:20',
      triageNotes: [
        'Current sick note expires when? Tomorrow.',
        'What is the condition? Anxiety and depression.',
        'Have you seen a therapist? Yes, weekly sessions.',
        'What does your therapist recommend? Another 4 weeks off work.',
        'Are you taking medication? Yes, Sertraline 100mg daily.'
      ]
    }
  },
  {
    id: '4',
    patientName: 'Robert Davies',
    dob: '05/06/1965',
    nhsNumber: '567 234 8901',
    requestType: 'Referral',
    priority: 'Normal',
    summary: 'Referral to dermatology for persistent skin rash on arms and legs. Present for 6 weeks, not responding to over-the-counter treatments.',
    timeReceived: '13:45',
    ageMinutes: 55,
    assignedTo: 'Dr. Patel',
    status: 'In Progress',
    phone: '+447788990011',
    postcode: 'L31 7YH'
  },
  {
    id: '5',
    patientName: 'Jennifer Parker',
    dob: '18/12/1988',
    nhsNumber: '678 345 0123',
    requestType: 'Test Result',
    priority: 'Normal',
    summary: 'Patient calling to inquire about blood test results taken last week. Routine diabetes check (HbA1c).',
    timeReceived: '13:30',
    ageMinutes: 70,
    status: 'Unassigned',
    phone: '+447556677889',
    postcode: 'L37 2QW'
  },
  {
    id: '6',
    patientName: 'Michael O\'Brien',
    dob: '28/04/1955',
    nhsNumber: '789 456 1234',
    requestType: 'Prescription',
    priority: 'Normal',
    summary: 'Repeat prescription for blood pressure medication (Ramipril 5mg). Pharmacy is Lloyds on Church Street.',
    timeReceived: '13:12',
    ageMinutes: 88,
    assignedTo: 'Prescribing Team',
    status: 'In Progress',
    phone: '+447445566778',
    postcode: 'L12 5RT'
  },
  {
    id: '7',
    patientName: 'Lisa Anderson',
    dob: '14/07/1998',
    nhsNumber: '890 567 2345',
    requestType: 'Appointment',
    priority: 'High',
    summary: 'Suspected UTI with severe symptoms. Burning urination, frequency, and lower abdominal pain for 3 days. Getting worse.',
    timeReceived: '12:55',
    ageMinutes: 105,
    status: 'Unassigned',
    hasRedFlag: true,
    phone: '+447334455667',
    postcode: 'L8 9TY'
  },
  {
    id: '8',
    patientName: 'David Phillips',
    dob: '09/02/1972',
    nhsNumber: '901 678 3456',
    requestType: 'Admin',
    priority: 'Low',
    summary: 'Request for copy of medical records for insurance application. Needs last 5 years of records.',
    timeReceived: '12:40',
    ageMinutes: 120,
    assignedTo: 'Admin Team',
    status: 'In Progress',
    phone: '+447223344556',
    postcode: 'L3 4HG'
  }
];

interface RequestQueueProps {
  onSelectRequest: (request: Request) => void;
  selectedRequestId: string | null;
}

export function RequestQueue({ onSelectRequest, selectedRequestId }: RequestQueueProps) {
  const [activeFilter, setActiveFilter] = useState<string>('all');

  const getRequestTypeColor = (type: string) => {
    const colors = {
      'Prescription': 'bg-purple-100 text-purple-700 border-purple-200',
      'Sick Note': 'bg-orange-100 text-orange-700 border-orange-200',
      'Referral': 'bg-teal-100 text-teal-700 border-teal-200',
      'Admin': 'bg-gray-100 text-gray-700 border-gray-200',
      'Test Result': 'bg-indigo-100 text-indigo-700 border-indigo-200',
      'Appointment': 'bg-blue-100 text-blue-700 border-blue-200'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-700';
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      'Urgent': 'bg-red-500 text-white',
      'High': 'bg-orange-500 text-white',
      'Normal': 'bg-blue-500 text-white',
      'Low': 'bg-gray-400 text-white'
    };
    return colors[priority as keyof typeof colors] || 'bg-gray-400 text-white';
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'Unassigned': 'bg-gray-100 text-gray-700',
      'In Progress': 'bg-blue-100 text-blue-700',
      'Resolved': 'bg-green-100 text-green-700',
      'Overdue': 'bg-red-100 text-red-700'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-700';
  };

  const getAgeColor = (minutes: number) => {
    if (minutes < 15) return 'text-green-600';
    if (minutes < 30) return 'text-amber-600';
    return 'text-red-600';
  };

  const filterRequests = (requests: Request[]) => {
    switch (activeFilter) {
      case 'urgent':
        return requests.filter(r => r.priority === 'Urgent' || r.hasRedFlag);
      case 'overdue':
        return requests.filter(r => r.status === 'Overdue' || r.ageMinutes > 60);
      case 'unassigned':
        return requests.filter(r => r.status === 'Unassigned');
      case 'resolved':
        return requests.filter(r => r.status === 'Resolved');
      default:
        return requests.filter(r => r.status !== 'Resolved');
    }
  };

  const filteredRequests = filterRequests(mockRequests);

  return (
    <div className="flex-1 flex flex-col bg-white overflow-hidden">
      {/* Filter Tabs - Sticky */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 flex-shrink-0">
        <div className="px-6 pt-4">
          <Tabs value={activeFilter} onValueChange={setActiveFilter}>
            <TabsList className="h-12">
              <TabsTrigger value="all" className="gap-2">
                All Open
                <Badge variant="secondary" className="ml-1">{mockRequests.filter(r => r.status !== 'Resolved').length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="urgent" className="gap-2">
                <AlertTriangle className="w-4 h-4" />
                Urgent
                <Badge variant="secondary" className="ml-1">{mockRequests.filter(r => r.priority === 'Urgent' || r.hasRedFlag).length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="overdue" className="gap-2">
                Overdue
                <Badge variant="secondary" className="ml-1">{mockRequests.filter(r => r.status === 'Overdue' || r.ageMinutes > 60).length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="unassigned" className="gap-2">
                Unassigned
                <Badge variant="secondary" className="ml-1">{mockRequests.filter(r => r.status === 'Unassigned').length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="resolved">
                Resolved Today
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Request Type Filter */}
        <div className="px-6 py-3 flex items-center gap-2 border-t border-gray-100">
          <span className="text-xs font-medium text-gray-600">Filter by type:</span>
          <div className="flex flex-wrap gap-2">
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-purple-50 bg-purple-100 text-purple-700 border-purple-200"
            >
              Prescription
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-blue-50 bg-blue-100 text-blue-700 border-blue-200"
            >
              Appointment
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-orange-50 bg-orange-100 text-orange-700 border-orange-200"
            >
              Sick Note
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-teal-50 bg-teal-100 text-teal-700 border-teal-200"
            >
              Referral
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-indigo-50 bg-indigo-100 text-indigo-700 border-indigo-200"
            >
              Test Result
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-gray-50 bg-gray-100 text-gray-700 border-gray-200"
            >
              Admin
            </Badge>
          </div>
        </div>
      </div>

      {/* Request List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-3">
        {filteredRequests.map((request) => (
          <Card
            key={request.id}
            className={`p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedRequestId === request.id ? 'ring-2 ring-blue-500 bg-blue-50' : ''
            }`}
            onClick={() => onSelectRequest(request)}
          >
            <div className="space-y-3">
              {/* Header Row */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {request.hasRedFlag && (
                      <Badge className="bg-red-500 text-white px-2 py-0.5">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        RED FLAG
                      </Badge>
                    )}
                    <Badge className={getPriorityColor(request.priority)}>
                      {request.priority}
                    </Badge>
                    <Badge variant="outline" className={getRequestTypeColor(request.requestType)}>
                      {request.requestType}
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-gray-900">{request.patientName}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      DOB: {request.dob}
                    </span>
                    <span className="flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5" />
                      NHS: {request.nhsNumber}
                    </span>
                    <span className="flex items-center gap-1">
                      <Phone className="w-3.5 h-3.5" />
                      {request.phone}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm text-gray-600 mb-1">{request.timeReceived}</div>
                  <div className={`text-xs font-medium ${getAgeColor(request.ageMinutes)}`}>
                    <Clock className="w-3 h-3 inline mr-1" />
                    {request.ageMinutes} min ago
                  </div>
                </div>
              </div>

              {/* Summary */}
              <p className="text-sm text-gray-700 line-clamp-2">{request.summary}</p>

              {/* Footer Row */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                <div className="flex items-center gap-3">
                  <Badge variant="secondary" className={getStatusColor(request.status)}>
                    {request.status}
                  </Badge>
                  {request.assignedTo && (
                    <span className="text-xs text-gray-600 flex items-center gap-1">
                      <User className="w-3.5 h-3.5" />
                      {request.assignedTo}
                    </span>
                  )}
                </div>

                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                  View Details
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
