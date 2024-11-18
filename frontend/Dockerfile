# Stage 1: Build the React app
FROM node:18-alpine as build

WORKDIR /app

# Define arguments to accept the API URL and PUBLIC_URL
ARG REACT_APP_API_URL
ARG PUBLIC_URL

# Make the arguments available as environment variables
ENV REACT_APP_API_URL=$REACT_APP_API_URL
#ENV PUBLIC_URL=$PUBLIC_URL

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci --production

# Copy the rest of the app and build
COPY . ./

# Build the React app
RUN npm run build
