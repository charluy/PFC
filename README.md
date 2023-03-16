# Py5cheSim v2.0

Py5cheSim es un simulador para redes 5G desarrollado en *Python*, flexible y de código abierto. El mismo está basado en *SimPy*, el cual es un *framework* para la simulación de eventos discretos y es utilizado para simular el envío y recepción de paquetes. Su objetivo es generar métricas de rendimiento a nivel de celda sobre *schedulers* implementados por el usuario en una configuración establecida, evitando así la necesidad de llevarlo a un ambiente real. El mismo está enfocado en la asignación de recursos entre diferentes usuarios y servicios con diferentes requerimientos.

## ¿Qué hay de nuevo en la versión 2?

En esta nueva versión se integró el *framework* DeepMIMO para obtener canales más realistas entre usuarios con movimiento y radio bases. Obteniendo de esta manera un canal selectivo en frecuencia y que varía en el tiempo en según un movimiento definido.

También se mejoró el soporte para SU-MIMO y MU-MIMO teniendo en cuenta el estado de canal para la asignación de *layers*. 

Estas nuevas características abrieron las puertas para que se puedan evaluar la performance de *schedulers* que tengan en cuenta el estado detallado del canal. Por esta razón se implementó un *intra slice scheduler* que utiliza estos nuevos datos y sirve como ejemplo para implementaciones posteriores.

Por último y alineado con el punto anterior, ahora el simulador también devuelve como salida una grilla de uso de los recursos físicos entre los diferentes usuarios.

## Instalación sugerida

Para utilizar este simulador es necesario contar con un intérprete de Python 3 instalado y realizar las siguientes acciones:

  - Abrir una consola y cambiar el directorio de trabaja a la raíz del proyecto.
  - Crear un ambiente virtual: `python3 -m venv env`
  - Instalar las dependencias del proyecto: `pip install -r requirements.txt`

## Procedimiento para realizar una simulación

En esta nueva versión la simulación se divide en dos etapas independientes:

  1. **Obtención de los datos del estado del canal**: a partir de los escenarios de DeepMIMO y de la definición que se realice de usuarios se obtienen archivos que contienen el estado del canal entre radio base y usuarios.

  2. **Ejecución de la simulación**: con los datos del canal obtenidos en la primera etapa, se define el perfil de tráfico de los usuarios junto con la selección de los *inter/intra slice schedulers* que se desee probar y se obtiene estadísticas de la performance de los mismos en ese escenario.

  A continuación se detallan ambas etapas.

  ### Obtención de los datos del estado del canal

Esta etapa de la simulación se puede realizar de dos maneras:

  1. **En un entorno local (_No recomendado_)**: Para esto es necesario [descargar el escenario de DeepMIMO](https://deepmimo.net/scenarios/) que se desea utilizar y colocarlo en el directorio `DeepMIMO/scenarios`. Luego solo falta configurar y ejecutar el script `channel_generator_{escenario_name}.py`.

  2. **En un entorno remoto (_Recomendado_)**: Para esto se debe subir a _Google Drive_ el notebook `notebook_channel_generator_{scenario_name}.py` que se desee ejecutar y seguir las instrucciones para que este tenga acceso a los archivos de DeepMIMO almacenados en el mismo servicio. Luego solo resta configurar los parámetros específicos y ejecutar las distintas celdas. Este método tiene la ventaja que no necesita descargar los archivos de los escenarios de DeepMIMO que en la mayoría de los casos son muy grandes.

En estos *scripts* se debe especificar los grupos de usuarios que se desea generar junto con la características de los mismos. Es decir, se debe especificar los siguientes puntos:

  1. Grupos de usuarios.
  2. Dirección y velocidad.
  2. Cantidad y forma de los elementos de antena en los paneles.
  3. Potencia de transmisión por subportadora.
  4. Nivel de piso de ruido.
  5. Frecuencia central de la portadora OFDM.
  6. Cantidad de escenas y tiempo entre las mismas.
  7. Radio base a utilizar.

En cualquiera de los casos se debe almacenar el resultado en el directorio `scenarios/`.

### Ejecución de la simulación



