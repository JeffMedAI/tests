import { X, Phone, MessageSquare, UserCheck, Users, Clipboard, AlertTriangle, ArrowUpCircle, FileText, Play, CheckCircle2, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import type { Request } from './RequestQueue';

interface DetailPanelProps {
  request: Request | null;
  onClose: () => void;
}

export function DetailPanel({ request, onClose }: DetailPanelProps) {
  if (!request) {
    return (
      <div className="w-[480px] bg-gray-50 border-l border-gray-200 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p className="text-sm">Select a request to view details</p>
        </div>
      </div>
    );
  }

  const getPriorityColor = (priority: string) => {
    const colors = {
      'Urgent': 'bg-red-500 text-white',
      'High': 'bg-orange-500 text-white',
      'Normal': 'bg-blue-500 text-white',
      'Low': 'bg-gray-400 text-white'
    };
    return colors[priority as keyof typeof colors] || 'bg-gray-400 text-white';
  };

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

  // Action buttons based on request type
  const getActionButtons = () => {
    const commonActions = (
      <>
        <Button variant="outline" size="sm" className="gap-2">
          <Phone className="w-4 h-4" />
          Call Back
        </Button>
        <Button variant="outline" size="sm" className="gap-2">
          <MessageSquare className="w-4 h-4" />
          Send SMS
        </Button>
        <Button variant="outline" size="sm" className="gap-2">
          <Clipboard className="w-4 h-4" />
          More Info
        </Button>
      </>
    );

    const typeSpecificActions = {
      'Prescription': (
        <Button variant="default" size="sm" className="gap-2 bg-purple-600 hover:bg-purple-700">
          <Users className="w-4 h-4" />
          Send to Prescribing
        </Button>
      ),
      'Appointment': (
        <Button variant="default" size="sm" className="gap-2 bg-blue-600 hover:bg-blue-700">
          <UserCheck className="w-4 h-4" />
          Send to GP
        </Button>
      ),
      'Sick Note': (
        <Button variant="default" size="sm" className="gap-2 bg-orange-600 hover:bg-orange-700">
          <UserCheck className="w-4 h-4" />
          Send to GP
        </Button>
      ),
      'Referral': (
        <Button variant="default" size="sm" className="gap-2 bg-teal-600 hover:bg-teal-700">
          <UserCheck className="w-4 h-4" />
          Send to GP
        </Button>
      ),
      'Admin': (
        <Button variant="default" size="sm" className="gap-2 bg-gray-600 hover:bg-gray-700">
          <Users className="w-4 h-4" />
          Send to Admin
        </Button>
      ),
      'Test Result': (
        <Button variant="default" size="sm" className="gap-2 bg-indigo-600 hover:bg-indigo-700">
          <UserCheck className="w-4 h-4" />
          Send to GP
        </Button>
      )
    };

    return (
      <>
        {commonActions}
        {typeSpecificActions[request.requestType as keyof typeof typeSpecificActions]}
      </>
    );
  };

  return (
    <div className="w-[480px] bg-white border-l border-gray-200 flex flex-col h-full flex-shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {request.hasRedFlag && (
                <Badge className="bg-red-500 text-white">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  RED FLAG
                </Badge>
              )}
              <Badge className={getPriorityColor(request.priority)}>
                {request.priority} Priority
              </Badge>
            </div>
            <h2 className="font-semibold text-lg text-gray-900">{request.patientName}</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="space-y-1.5 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">DOB:</span>
            <span className="font-medium text-gray-900">{request.dob}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">NHS Number:</span>
            <span className="font-medium text-gray-900">{request.nhsNumber}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Phone:</span>
            <span className="font-medium text-gray-900">{request.phone}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Postcode:</span>
            <span className="font-medium text-gray-900">{request.postcode}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Request Type:</span>
            <Badge variant="outline" className={getRequestTypeColor(request.requestType)}>
              {request.requestType}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Time Received:</span>
            <span className="font-medium text-gray-900">{request.timeReceived}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Age:</span>
            <span className="font-medium text-red-600">{request.ageMinutes} minutes</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex flex-wrap gap-2">
          {getActionButtons()}
          {request.hasRedFlag && (
            <Button variant="destructive" size="sm" className="gap-2 w-full mt-2">
              <ArrowUpCircle className="w-4 h-4" />
              Escalate Urgent
            </Button>
          )}
          <Button variant="default" size="sm" className="gap-2 w-full bg-green-600 hover:bg-green-700">
            <CheckCircle2 className="w-4 h-4" />
            Mark as Resolved
          </Button>
        </div>
      </div>

      {/* Content Tabs */}
      <div className="flex-1 overflow-y-auto">
        <Tabs defaultValue="summary" className="h-full flex flex-col">
          <TabsList className="w-full justify-start rounded-none border-b">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="triage">Triage</TabsTrigger>
            <TabsTrigger value="transcript">Transcript</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto">
            <TabsContent value="summary" className="p-4 space-y-4 m-0">
              <Card className="p-4">
                <h3 className="font-semibold text-gray-900 mb-2">AI Summary</h3>
                <p className="text-sm text-gray-700 leading-relaxed">{request.summary}</p>
              </Card>

              {request.hasRedFlag && (
                <Card className="p-4 bg-red-50 border-red-200">
                  <div className="flex gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-red-900 mb-1">Red Flag Warning</h3>
                      <p className="text-sm text-red-700">This request has been flagged for urgent clinical attention. Immediate review recommended.</p>
                    </div>
                  </div>
                </Card>
              )}

              <Card className="p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Suggested Actions</h3>
                <div className="space-y-2 text-sm">
                  {request.requestType === 'Prescription' && (
                    <>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                        <span>Verify prescription details and current supply</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                        <span>Check for drug interactions</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                        <span>Forward to prescribing team for approval</span>
                      </div>
                    </>
                  )}
                  {request.requestType === 'Appointment' && (
                    <>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                        <span>Assess urgency and triage category</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                        <span>Check for red flag symptoms</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                        <span>Route to appropriate GP for review</span>
                      </div>
                    </>
                  )}
                </div>
              </Card>
            </TabsContent>

            <TabsContent value="triage" className="p-4 space-y-3 m-0">
              {request.detailedInfo?.triageNotes ? (
                request.detailedInfo.triageNotes.map((note, idx) => (
                  <Card key={idx} className="p-3">
                    <p className="text-sm text-gray-700">{note}</p>
                  </Card>
                ))
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">No triage information available</p>
              )}
            </TabsContent>

            <TabsContent value="transcript" className="p-4 space-y-4 m-0">
              {request.detailedInfo?.duration && (
                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <button className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center hover:bg-green-600">
                      <Play className="w-5 h-5 text-white ml-0.5" />
                    </button>
                    <div className="flex-1">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Call Recording</span>
                        <span>{request.detailedInfo.duration}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{ width: '40%' }}></div>
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {request.detailedInfo?.conversation ? (
                <div className="space-y-3">
                  {request.detailedInfo.conversation.map((msg, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className={`font-semibold text-sm ${msg.speaker === 'VA' ? 'text-blue-600' : 'text-gray-900'}`}>
                        {msg.speaker}:
                      </div>
                      <Card className="p-3 bg-gray-50">
                        <p className="text-sm text-gray-700">{msg.text}</p>
                      </Card>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">No transcript available</p>
              )}
            </TabsContent>

            <TabsContent value="history" className="p-4 space-y-3 m-0">
              <Card className="p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Contact History</h3>
                <div className="space-y-3">
                  <div className="flex gap-3 text-sm">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Phone className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">Today at {request.timeReceived}</div>
                      <div className="text-gray-600">Request created: {request.requestType}</div>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Audit Trail</h3>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>Request received: {request.timeReceived}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>Status: {request.status}</span>
                  </div>
                  {request.assignedTo && (
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>Assigned to: {request.assignedTo}</span>
                    </div>
                  )}
                </div>
              </Card>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
