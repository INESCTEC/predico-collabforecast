FROM nginx

RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/

RUN rm /etc/nginx/conf.d/default.conf
COPY project.conf /etc/nginx/conf.d/

COPY certificate.pem /etc/nginx/ssl/certificate.pem
COPY private.key /etc/nginx/ssl/private.key

# Expose port 443
EXPOSE 443