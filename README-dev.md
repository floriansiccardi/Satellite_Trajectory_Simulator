ReadMe Développeur
==================

Le document suivant décrit globalement le fonctionnement du simulateur, à travers différents aspects :

<br />**Méthode d'intégration**
-------------------------------
<br /><br />La méthode d'intégration est le schéma d'Euler avant :

$\frac{\partial x}{\partial t}(t) = \lim_{dt\rightarrow 0} \frac{x(t+dt)-x(t)}{dt} \simeq  \frac{x(t+dt)-x(t)}{dt}$
    
<br />Soit, pour la position : $x(t+dt) \simeq x(t) + dt \ \frac{\partial x}{\partial t}(t)$
<br />De même pour la vitesse : $v(t+dt) \simeq v(t) + dt \ \frac{\partial v}{\partial t}(t)$
<br />Où $\frac{\partial v}{\partial t}(t) = a(t) = \frac{1}{m} \sum F_{i}(t) = a_{grav}(t) + \frac{1}{m} \sum T_{thrust}(t)$

____________________
<br />**Méthode itérative**
---------------------------
<br /><br />A chaque itération, le simulateur va procéder par les étapes suivantes :
<br />&ensp;> Intégrer la position/vitesse des satellites. Pour chacun d'entre eux, le simulateur va :
<br />&ensp;&ensp;&ensp;- Calculer la nouvelle accélération (gravité + propulseurs)
<br />&ensp;&ensp;&ensp;- Intégrer la position/vitesse
<br />&ensp;&ensp;&ensp;- Mettre à jour les axes propres au satellite
<br />&ensp;&ensp;&ensp;- Vérifier les collisions avec les autres objets
<br />&ensp;&ensp;&ensp;- Mettre à jour les contrôles manuels du satellite (du l'utilisateur)
<br />&ensp;> Mettre à jour les contrôles du simulateur (ex: changement de pas de temps)
<br />&ensp;> Mettre à jour les contrôles automatiques du satellite (du contrôleur)

____________________
<br />**Classe Contrôleur**
---------------------------
<br /><br />La classe contrôleur permet de guider automatiquement le satellite selon les demandes de l'utilisateur. Il permet de gérer la puissance de tous les propulseurs, afin de réaliser les manoeuvres demandées par l'utilisateur.
<br /><br />Les équations de calcul de puissances nécessaires à une accélération sont les suivantes :
<br />$\Delta \dot{x}=\dot{x}(t+n\ dt)-\dot{x}(t)=n\ \ddot{x}\ dt$, pour $dt$ et $\ddot{x}$ constant sur les $n$ itérations
<br />$F=\ddot{x}\ m=\frac{\Delta \dot{x}\ m}{n\ dt}=\phi\ F_{max}$
<br />$\Leftrightarrow \phi\ = \frac{1}{n\ dt} \frac{\Delta \dot{x}\ m}{F_{max}}$
<br />Où $min(n),\ 0 \leqslant \phi \leqslant 1 \Rightarrow n=ceil(\phi\ n)=ceil(\frac{1}{dt}\frac{\Delta \dot{x}\ m}{F_{max}})$
<br /><br />De manière similaire pour la rotation :
<br />$\Delta \dot{\alpha}=\dot{\alpha}(t+n\ dt)-\dot{\alpha}(t)=n\ \ddot{\alpha}\ dt$, pour $dt$ et $\ddot{\alpha}$ constant sur les $n$ itérations
<br />$\tau=\ddot{\alpha}\ I=\frac{\Delta \dot{\alpha}\ I}{n\ dt}=\phi\ \tau_{max}$
<br />$\Leftrightarrow \phi\ = \frac{1}{n\ dt} \frac{\Delta \dot{\alpha}\ I}{\tau_{max}}$
<br />Où $min(n),\ 0 \leqslant \phi \leqslant 1 \Rightarrow n=ceil(\phi\ n)=ceil(\frac{1}{dt}\frac{\Delta \dot{\alpha}\ I}{\tau_{max}})$
<br /><br />Pour les transfert d'Hohmann, les équations suivantes ont été utilisées :
<br />$v_1 = \sqrt{2\ G\ M\ (\frac{1}{r_1}-\frac{1}{r_1+r_2})}$
<br />$v_2 = \sqrt{2\ G\ M\ (\frac{1}{r_2}-\frac{1}{r_1+r_2})}$
<br /><br />D'autres formules ont été utilisés afin de déterminer des grandeurs en temps réel :
<br />$v_{geo}=\sqrt{\frac{G\ M}{r}}$
<br />$T_{geo}=\frac{2\pi\ r}{v}=2\pi\ \sqrt{\frac{r^3}{G\ M}}$
<br />$T_{elliptic}=2\pi\ \sqrt{\frac{1}{G\ M}(\frac{r_1+r_2}{2})^3}$
<br /><br />Enfin, pour rejoindre une orbite géo-stationnaire, le contrôleur exerce une puissance de telle sorte à avoir un accélération constante, dans le sens radial, proportionnelle à son poids actuel :
<br />$\vec{a}(t)=a_r(t)\ \vec{u_r}(t)=\gamma_1\ a_g(t)\ m\ \vec{u_r}(t)$, où $a_r(t) > 0$
<br />Pour maintenir cette accélération, généralement avec $\gamma_1 = 1$%, le contrôleur utilise la seconde loi de Newton :
<br />$a_r(t) = \sum \vec{F}(t) \cdot \vec{u_r} =-a_g(t)\ m\ +\ T=\gamma_1\ a_g(t)\ m$
<br />Ce qui donne : $T=(\gamma_1+1)\ a_g(t)\ m$
<br /><br />Durant la seconde phase, pour obtenir une certaines accélérations tangentielle, le contrôleur se base sur les équations suivantes :
<br />$\vec{a}(t)=a_r(t)\ \vec{u_r}(t) + \vec{a_t}(t)=\gamma_2\ a_g(t)\ m\ \vec{u_r}(t) + \vec{a_t}(t)$, où $a_r(t) > 0$
<br />En utilisant aussi la seconde loi de Newton :
<br />$a_r(t) = \sum \vec{F}(t) \cdot \vec{u_r} =-a_g(t)\ m\ +\ T\ cos(\theta) + \frac{m\ v^2}{r}\ sin^2(\theta)=\gamma_2\ a_g(t)\ m$
<br />Ce qui donne : $T = [(\gamma_2+1)a_g(t)-\frac{v^2}{r}sin^2(\theta))]\frac{m}{cos(\theta)}$
<br />Et permet d'avoir : $a_t(t) = \frac{T\ sin(\theta)}{m}\ > 0$
