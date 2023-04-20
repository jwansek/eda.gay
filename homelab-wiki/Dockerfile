FROM mediawiki:1.39.3

ENV MW_HOME=/var/www/html

# download and add composer to path
RUN set -x; \
    php -r "readfile('https://getcomposer.org/installer');" | php \
    && mv composer.phar /usr/local/bin/composer

# get skins
RUN set -x; \
    cd $MW_HOME/skins \
    && git clone https://github.com/StarCitizenTools/mediawiki-skins-Citizen Citizen

# get extensions
RUN set -x; \
    cd $MW_HOME/extensions \
    && git clone --depth 1 -b REL1_39 https://github.com/wikimedia/mediawiki-extensions-TemplateStyles \ 
    && git clone --depth 1 https://github.com/Universal-Omega/PortableInfobox.git

# install extensions
RUN set -x; \
    cd $MW_HOME/extensions/mediawiki-extensions-TemplateStyles \
    && composer install --no-dev