

----------------------------------------------------------------------------------------------------------------------------------

#cuenta 1

ACCOUNT="github.com"
USERNAME="1di210299"
REPO="mvp"
git clone git@${ACCOUNT}:${USERNAME}/${REPO}.git

#cuenta 2
ssh -T git@theseus.github.com
cd ~

ACCOUNT="theseus.github.com"
USERNAME="theseus-group"
REPO="theseus-public-website-stack"
git clone git@${ACCOUNT}:${USERNAME}/${REPO}.git

----------------------------------------------------------------------------------------------------------------------------------


#ejemplo 1

ssh -T git@theseus.github.com
cd ~
rm -rf AppSwipper Documents/AppSwipper
git clone git@theseus.github.com:theseus-group/AppSwipper.git

# ejemplo 2
ssh -T git@github.com

git clone git@theseus.github.com:theseus-group/theseus-public-website-stack.git
rm -rf theseus-public-website-stack Documents/theseus-public-website-stack

git config --global user.name "1di210299"
git config --global user.email "juand.gutierrezc@pucp.edu.pe"


git config --global user.name "JuanDi-oss"
git config --global user.email "juan@theseus.earth"

git config --global JuanDi-oss
git config --global juan@theseus.earth


git config --global user.name "miguel5872"
git config --global user.email "orbegoso.unmsm@gmail.com"
