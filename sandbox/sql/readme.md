
# Création du dump 

Une fois que votre base de donnée bac à sable est créée 
il vous fuat utiliser la commande pg_dump avec les bons crédentials :


  pg_dump -U username dbname > dbexport.pgsql

# déplacement du fichier

SANDBOX= whereever you put the sandbox git repository 

mv dbexport.pgsql    $SANDBOX/sandbox/docker/

# relancer la commande de création du docker

cd $SANDBOX/sandbox/docker/

docker build -t pl:sql -f DockerfileSQL

# Settings 

préciser que c'est le docker que vous voulez utiliser dans la sanbdox 
editez 
$SANDBOX/pl_sandbox/settings.py 
remplacer la ligne 
DOCKER_IMAGE = "pl:base"
par 
DOCKER_IMAGE = "pl:sql"

