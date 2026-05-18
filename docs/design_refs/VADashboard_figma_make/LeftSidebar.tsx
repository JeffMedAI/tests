import { useState } from 'react';
import { Clock, AlertTriangle, CheckCircle2, TrendingUp, Phone, PhoneOff, PhoneMissed, FileText, Pill, Stethoscope, ClipboardList, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  status?: 'success' | 'warning' | 'danger' | 'neutral';
  change?: string;
  isCollapsed?: boolean;
}

function KPICard({ title, value, icon, trend, status = 'neutral', change, isCollapsed = false }: KPICardProps) {
  const statusColors = {
    success: 'bg-green-50 text-green-700',
    warning: 'bg-amber-50 text-amber-700',
    danger: 'bg-red-50 text-red-700',
    neutral: 'bg-blue-50 text-blue-700'
  };

  if (isCollapsed) {
    return (
      <Card className="p-2">
        <div className="flex flex-col items-center gap-1">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${statusColors[status]}`}>
            {icon}
          </div>
          <div className="text-lg font-semibold text-gray-900">{value}</div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="text-xs text-gray-500 mb-1">{title}</div>
          <div className="text-xl font-semibold text-gray-900">{value}</div>
          {change && (
            <div className={`text-xs mt-1 ${change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
              {change} vs yesterday
            </div>
          )}
          {trend && !change && (
            <div className="text-xs text-gray-500 mt-1">{trend}</div>
          )}
        </div>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${statusColors[status]}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}

export function LeftSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [dateFilter, setDateFilter] = useState<string>('today');

  const getDataForPeriod = (period: string) => {
    const data = {
      today: { open: 24, overdue: 5, resolved: 37, avgResponse: '8 min', avgResolution: '18 min', calls: 142, dropped: 3, transferred: 8 },
      week: { open: 156, overdue: 18, resolved: 234, avgResponse: '12 min', avgResolution: '22 min', calls: 892, dropped: 21, transferred: 45 },
      month: { open: 642, overdue: 78, resolved: 1024, avgResponse: '15 min', avgResolution: '25 min', calls: 3764, dropped: 89, transferred: 198 }
    };
    return data[period as keyof typeof data] || data.today;
  };

  const stats = getDataForPeriod(dateFilter);

  if (isCollapsed) {
    return (
      <div className="w-16 bg-gray-50 border-r border-gray-200 p-2 flex flex-col items-center gap-3 flex-shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(false)}
          className="mb-2"
        >
          <ChevronRight className="w-5 h-5" />
        </Button>
        <KPICard
          title="Open"
          value={stats.open}
          icon={<Clock className="w-4 h-4" />}
          status="warning"
          isCollapsed
        />
        <KPICard
          title="Overdue"
          value={stats.overdue}
          icon={<AlertTriangle className="w-4 h-4" />}
          status="danger"
          isCollapsed
        />
        <KPICard
          title="Resolved"
          value={stats.resolved}
          icon={<CheckCircle2 className="w-4 h-4" />}
          status="success"
          isCollapsed
        />
        <Card className="p-2 bg-red-50 border-red-200 mt-2">
          <div className="flex flex-col items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mb-1" />
            <div className="text-sm font-semibold text-red-700">4</div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-72 bg-gray-50 border-r border-gray-200 flex flex-col flex-shrink-0">
      {/* Header with collapse button */}
      <div className="p-3 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
        <h2 className="font-semibold text-gray-900">Analytics</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(true)}
        >
          <ChevronLeft className="w-5 h-5" />
        </Button>
      </div>

      {/* Date Range Filter */}
      <div className="p-3 border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center gap-2 mb-2">
          <Calendar className="w-4 h-4 text-gray-500" />
          <span className="text-xs font-medium text-gray-600">Time Period</span>
        </div>
        <Tabs value={dateFilter} onValueChange={setDateFilter} className="w-full">
          <TabsList className="grid grid-cols-3 w-full h-9">
            <TabsTrigger value="today" className="text-xs">Today</TabsTrigger>
            <TabsTrigger value="week" className="text-xs">Week</TabsTrigger>
            <TabsTrigger value="month" className="text-xs">Month</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Priority Stats - Above the fold */}
        <div>
          <h3 className="text-xs font-semibold text-gray-900 mb-2">Queue Status</h3>
          <div className="space-y-2">
            <KPICard
              title="Open Requests"
              value={stats.open}
              icon={<Clock className="w-5 h-5" />}
              status="warning"
              change="+12%"
            />
            <KPICard
              title="Overdue"
              value={stats.overdue}
              icon={<AlertTriangle className="w-5 h-5" />}
              status="danger"
              change="-8%"
            />
            <KPICard
              title={dateFilter === 'today' ? 'Resolved Today' : 'Total Resolved'}
              value={stats.resolved}
              icon={<CheckCircle2 className="w-5 h-5" />}
              status="success"
              change="+24%"
            />
          </div>
        </div>

        {/* Red Flags - Keep visible */}
        <Card className="p-3 bg-red-50 border-red-200">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-semibold text-red-900">Red Flags</div>
              <div className="text-2xl font-semibold text-red-700 mt-0.5">4</div>
              <div className="text-xs text-red-600 mt-0.5">Urgent attention</div>
            </div>
          </div>
        </Card>

        {/* Performance Metrics */}
        <div>
          <h3 className="text-xs font-semibold text-gray-900 mb-2">Performance</h3>
          <div className="space-y-2">
            <KPICard
              title="Avg First Response"
              value={stats.avgResponse}
              icon={<TrendingUp className="w-5 h-5" />}
              status="success"
              trend="Within SLA"
            />
            <KPICard
              title="Avg Resolution Time"
              value={stats.avgResolution}
              icon={<Clock className="w-5 h-5" />}
              status="success"
            />
          </div>
        </div>

        {/* Call Analytics with mini chart */}
        <div>
          <h3 className="text-xs font-semibold text-gray-900 mb-2">Call Analytics</h3>
          <Card className="p-3">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-blue-600" />
                  <span className="text-xs text-gray-700">Total Calls</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{stats.calls}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <PhoneOff className="w-4 h-4 text-amber-600" />
                  <span className="text-xs text-gray-700">Dropped</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{stats.dropped}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <PhoneMissed className="w-4 h-4 text-gray-600" />
                  <span className="text-xs text-gray-700">Transferred</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{stats.transferred}</span>
              </div>
            </div>

            {/* Success Rate Visual */}
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="text-xs text-gray-600 mb-1">Success Rate</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: '97.9%' }}></div>
                </div>
                <span className="text-xs font-semibold text-green-600">97.9%</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Request Type Breakdown with bars */}
        <div>
          <h3 className="text-xs font-semibold text-gray-900 mb-2">Request Types</h3>
          <Card className="p-3">
            <div className="space-y-2.5">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Pill className="w-3.5 h-3.5 text-purple-600" />
                    <span className="text-xs text-gray-700">Prescription</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-900">48</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: '34%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Stethoscope className="w-3.5 h-3.5 text-blue-600" />
                    <span className="text-xs text-gray-700">Appointment</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-900">38</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: '27%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-orange-600" />
                    <span className="text-xs text-gray-700">Sick Note</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-900">22</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-500 rounded-full" style={{ width: '16%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <ClipboardList className="w-3.5 h-3.5 text-teal-600" />
                    <span className="text-xs text-gray-700">Referral</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-900">15</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-teal-500 rounded-full" style={{ width: '11%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-gray-600" />
                    <span className="text-xs text-gray-700">Admin</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-900">19</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gray-500 rounded-full" style={{ width: '13%' }}></div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
