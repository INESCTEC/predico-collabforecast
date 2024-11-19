import React from 'react';
import logo from '../assets/images/PREDICO_LOGO_POSITIF.png'; // Update the path to your logo

const Logo = ({ containerClass = '', imageClass = '' }) => {
    return (
        <div className={`${containerClass}`}>
            <img
                alt="Predico"
                src={logo}
                className={`${imageClass}`}
            />
        </div>
    );
};

export default Logo;