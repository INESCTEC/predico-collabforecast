import { useAuth } from '../AuthContext';

export default function ErrorBanner() {
  
  const { error, clearError } = useAuth();
  
  if (!error) return null;  // Don't render anything if there's no error
  
  return (
    <div className="fixed top-0 left-0 right-0 bg-red-500 text-white p-3 z-50">
      <div className="container mx-auto flex justify-between items-center">
        <p>{error}</p>
        <button onClick={clearError} className="text-white">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
