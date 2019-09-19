Problema a resolver. Eleg� el problema "De gatos y ratones".

Lenguaje y entorno de desarrollo. El programa esta escrito en Python sin el
	uso de ning�n IDE, por lo que puede ser ejecutado en cualquier
	computadora con python instalado desde la terminal con el comando
	"Python tarea1.py".

Estrat�gias de sincroniaci�n. Escog� el problema ya que encontr�
	similitudes con los problemas de "Lector-Escritor" y "Los Filosofos",
	as� que implemnt� dos mecanismos:
	El Apagador para controlar el acceso de dos categor�as que son los
	gatos y los ratones, siendo el apagador la cocina.
	El Multiplex para llevar el control de los platos.
	Sin embargo, el programa no resuelve el problema planteado. No pude
	encontrar una forma de hacer que los ratones pudieran accesar aun
	cuando hay gatos en la cocina (para que sean comidos). Y en concecuencia
	de lo anterior jam�s llegu� a implementar la eliminaci�n de un rat�n
	(que ten�a planeado matar el hilo).

Refinamientos. Un problema muy com�n al ejecutar mi programa es que si un
	grupo entraba a comer provocaba inanici�n al otro. Intent� controlar
	esta situaci�n con un contador pero solo empeor� la efectividad del
	programa haciendolo m�s largo y ahora no hay control de que grupo entra
	a la cocina.

Dudas. Mi mayor duda que no pude resolver fue como controlar el acceso a la
	cocina en un solo sentido, es decir que los gatos no puedan acceder
	cuando hay ratones, pero que los ratones si tengan la opci�n de entrar
	(para cumplir el requisito de que sean comidos). Previamente intent�
	resolverlo poniendole como condicional al gato una variable de cuantos
	ratones hay en la cocina y para acceder usar el mutex de los ratones,
	sin embargo, ocacion� un bloqueo mutuo poniendo a dormir a todos los
	ratones y gatos. 