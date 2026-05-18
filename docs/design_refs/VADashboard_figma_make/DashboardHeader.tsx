import { User, Search } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Checkbox } from './ui/checkbox';
import logo from "figma:asset/55aee39f36dc806edb896a5be8d365e30b475d5b.png";

export function DashboardHeader() {
  return (
    <div className="bg-blue-500 text-white p-6">
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-white rounded-full"></div>
          <div>
            <h1 className="text-2xl font-bold">CHURCHTOWN MEDICAL CENTRE</h1>
            <p className="text-sm text-blue-100">02 February 2025</p>
          </div>
        </div>
        <button className="w-10 h-10 bg-blue-400 rounded-full flex items-center justify-center hover:bg-blue-300 transition">
          <User className="w-6 h-6" />
        </button>
      </div>
      
      <div className="grid grid-cols-[1fr_1fr_1fr_2fr_auto] gap-3 items-end">
        <div>
          <label className="text-xs text-blue-100 mb-1 block">Request type</label>
          <Select defaultValue="all">
            <SelectTrigger className="bg-white text-gray-800">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="prescription">Prescription</SelectItem>
              <SelectItem value="appointment">Appointment</SelectItem>
              <SelectItem value="sick-note">Sick Note</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <label className="text-xs text-blue-100 mb-1 block">Status</label>
          <Select defaultValue="all">
            <SelectTrigger className="bg-white text-gray-800">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <label className="text-xs text-blue-100 mb-1 block">Date range</label>
          <Select defaultValue="all">
            <SelectTrigger className="bg-white text-gray-800">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <label className="text-xs text-blue-100 mb-1 block">Search</label>
          <Input 
            type="text" 
            placeholder="Search by Patient name, NHS number or Phone number" 
            className="bg-white text-gray-800"
          />
        </div>
        
        <div className="flex items-center gap-2 text-sm pb-2">
          <Checkbox id="incomplete" className="border-white data-[state=checked]:bg-white data-[state=checked]:text-blue-500" />
          <label htmlFor="incomplete" className="cursor-pointer">Incomplete requests</label>
        </div>
      </div>
    </div>
  );
}
