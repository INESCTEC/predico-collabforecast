import { ChevronRightIcon, Cog6ToothIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { Dialog, DialogPanel, Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/react';
import { NavLink, useLocation } from 'react-router-dom'; // Import NavLink and useLocation for route checks
import logo from '../assets/images/elia-group-logo-svg.svg'; // Path to your logo

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function Sidebar({ navigation, sidebarOpen, setSidebarOpen }) {
  return (
    <>
      {/* Mobile sidebar */}
      <Dialog open={sidebarOpen} onClose={setSidebarOpen} className="relative z-50 lg:hidden">
        <div className="fixed inset-0 bg-gray-900/80" />
        <div className="fixed inset-0 flex">
          <DialogPanel className="relative mr-16 flex w-full max-w-xs flex-1 bg-white">
            <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
              <button type="button" onClick={() => setSidebarOpen(false)} className="-m-2.5 p-2.5">
                <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
              </button>
            </div>
            <div className="flex flex-col gap-y-5 overflow-y-auto p-6 pb-4 bg-gradient-to-b from-orange-100 via-white to-orange-200">
              <div className="flex h-16 items-center">
                <img src={logo} alt="Your Company" className="h-8 w-auto" />
              </div>
              <NavigationList navigation={navigation} />
            </div>
          </DialogPanel>
        </div>
      </Dialog>
      
      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-72 lg:flex-col lg:border-r lg:border-gray-200 bg-gradient-to-b from-orange-100 via-white to-orange-200">
        <div className="flex flex-col gap-y-5 overflow-y-auto p-6 pb-4">
          <div className="flex h-16 items-center">
            <img src={logo} alt="Your Company" className="h-8 w-auto" />
          </div>
          <NavigationList navigation={navigation} />
        </div>
      </div>
    </>
  );
}

function NavigationList({ navigation }) {
  const location = useLocation(); // Get the current location to check the route
  
  return (
    <nav className="flex-1">
      <ul className="flex flex-col gap-y-7">
        <li>
          <ul className="-mx-2 space-y-1">
            {navigation.map((item) => {
              const isActiveParent = item.children && item.children.some((subItem) => location.pathname === subItem.href);
              const isAnySubItemActive = item.children && location.pathname.startsWith(item.href);
              
              return (
                <li key={item.name}>
                  {!item.children ? (
                    <NavLink
                      to={item.href}
                      className={({ isActive }) =>
                        classNames(
                          isActive
                            ? 'bg-orange-300 text-orange-800'  // Active link background and text color
                            : 'text-gray-700 hover:bg-orange-200 hover:text-orange-900',
                          'group flex items-center justify-between gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                        )
                      }
                    >
                      <div className="flex items-center gap-x-3">
                        <item.icon className="h-6 w-6 text-gray-400 group-hover:text-orange-900" /> {/* Icon hover color */}
                        {item.name}
                      </div>
                    </NavLink>
                  ) : (
                    <Disclosure as="div" className="space-y-1" defaultOpen={isActiveParent}>
                      {({ open }) => (
                        <>
                          <DisclosureButton
                            className={classNames(
                              'group flex w-full items-center justify-between gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700',
                              isActiveParent || (open && isAnySubItemActive) ? 'bg-orange-200 text-orange-900' : 'hover:bg-orange-200 hover:text-orange-900'
                            )}
                          >
                            <div className="flex items-center gap-x-3">
                              <item.icon className="h-6 w-6 text-gray-400 group-hover:text-orange-900" />
                              {item.name}
                            </div>
                            <ChevronRightIcon
                              className={classNames(
                                open ? 'rotate-90 text-gray-500' : 'text-gray-400',
                                'h-5 w-5 shrink-0 transform transition-transform'
                              )}
                              aria-hidden="true"
                            />
                          </DisclosureButton>
                          <DisclosurePanel as="ul" className="mt-1 space-y-1">
                            {item.children.map((subItem) => (
                              <li key={subItem.name}>
                                <NavLink
                                  to={subItem.href}
                                  className={({ isActive }) =>
                                    classNames(
                                      isActive
                                        ? 'bg-orange-300 text-orange-800'  // Active link background and text color for sub-items
                                        : 'hover:bg-orange-200 hover:text-orange-900',
                                      'block rounded-md py-2 pl-10 pr-2 text-sm leading-6 text-gray-700'
                                    )
                                  }
                                >
                                  {subItem.name}
                                </NavLink>
                              </li>
                            ))}
                          </DisclosurePanel>
                        </>
                      )}
                    </Disclosure>
                  )}
                </li>
              );
            })}
          </ul>
        </li>
        <li className="mt-auto">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              classNames(
                isActive ? 'bg-orange-300 text-orange-800' : 'text-gray-700 hover:bg-orange-200 hover:text-orange-900',
                'group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
              )
            }
          >
            <Cog6ToothIcon className="h-6 w-6 shrink-0 text-gray-400 group-hover:text-orange-900" aria-hidden="true" />
            Settings
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
