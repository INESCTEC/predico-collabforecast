// components/Header.js
import {Menu, MenuButton, MenuItem, MenuItems} from '@headlessui/react';
import {Bars3Icon, ChevronDownIcon, UserCircleIcon} from '@heroicons/react/24/outline'; // Import UserIcon
import {fetchUserDetails} from "../slices/userSlice";
import {useDispatch, useSelector} from "react-redux";
import {useEffect} from "react";

export default function Header({ setSidebarOpen, userNavigation }) {
  
  const { userDetails } = useSelector(state => state.user);
  
  const dispatch = useDispatch()
  useEffect(() => {
    dispatch(fetchUserDetails())
  }, [dispatch])
  
  
  return (
    <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 bg-white shadow-sm px-4 sm:gap-x-6 lg:gap-x-8">
      <button
        type="button"
        onClick={() => setSidebarOpen(true)}
        className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
      >
        <Bars3Icon className="h-6 w-6" aria-hidden="true"/>
      </button>
      
      <div className="flex flex-1 justify-end gap-x-4 lg:gap-x-6">
        {/*<button className="text-gray-400 hover:text-gray-500">*/}
        {/*  <BellIcon className="h-6 w-6" aria-hidden="true" />*/}
        {/*</button>*/}
        
        <Menu as="div" className="relative">
          <MenuButton className="flex items-center">
            {/* Replace image with UserIcon */}
            <UserCircleIcon className="h-8 w-8 text-gray-400" aria-hidden="true"/>
            
            <span className="hidden lg:flex lg:items-center">
          <span className="ml-4 text-sm font-semibold text-gray-900">{userDetails.email}</span>
          <ChevronDownIcon className="ml-2 h-5 w-5 text-gray-400" aria-hidden="true"/>
        </span>
          </MenuButton>
          
          <MenuItems
            className="absolute right-0 z-10 mt-2.5 w-32 origin-top-right bg-white py-2 shadow-lg ring-1 ring-black ring-opacity-5">
            {userNavigation.map((item) => (
              <MenuItem key={item.name}>
                <a href={item.href}
                   className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                   onClick={() => item.onClick && item.onClick()}>
                  {item.name}
                </a>
              </MenuItem>
            ))}
          </MenuItems>
        </Menu>
      </div>
    </div>
  );
}
