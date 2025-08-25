# Visão Geral

Os tutoriais do Cortex oferecem uma visão geral abrangente da estrutura e dos conceitos por trás dela.
Essa é a melhor introdução. Aqui, descrevemos brevemente alguns destaques e especificidades da extensão.

As ferramentas do Cortex fornecem uma estrutura de decisão para orquestrar as ferramentas fornecidas no Isaac Sim para projetar comportamento e executá-lo em robôs físicos. Ela consiste em:
- Um executor principal do loop do Cortex. Esta é a mente do robô, com um modelo de crença do mundo e
do próprio robô, e ferramentas para analisar o estado lógico do mundo e escolher ações. Ele usa
ferramentas de geração de movimento incorporadas ao Isaac Sim para controlar o robô de crença.
- Uma extensão `cortex_ros` que conecta essa crença de e para o mundo físico usando ROS.
A percepção transforma o fluxo de entrada no modelo de crença, e os fluxos de atuação são enviados para o robô físico.
- Uma extensão `cortex_sim` que representa uma versão simulada do mundo real para desenvolvimento de software e hardware no loop. Ele implementa os protocolos de interface ROS esperados do sistema de controle do robô físico e do módulo de percepção do mundo real.
- Alguns exemplos de ambientes e comportamentos, incluindo um mundo de blocos e scripts que implementam um comportamento de empilhamento de blocos reativo, demonstrando a estrutura de decisão do Cortex.

# Início rápido -- demonstração de empilhamento de blocos

A seguir, uma breve visão geral da execução do sistema usando a demonstração de empilhamento de blocos Franka como exemplo.

Esses comandos são relativos a `standalone_examples/cortex`.

Observação: Ao iniciar vários terminais, conforme descrito abaixo, é conveniente usar o aplicativo `Terminator`.

## Iniciando o sistema apenas com o robô de crença

Executando apenas um robô de crença. Inicia o executor de loop do Cortex principal sem ROS (padrão).
```
Terminal 1: Inicia o executor de loop do Cortex passando no ambiente USD do mundo de blocos.
    cd standalone_examples/cortex
    ./cortex launch --usd_env=Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd

# O script `cortex` é um alias para o executor de loop `cortex_main.py`. Alternativamente, a partir do diretório base do Isaac Sim, você pode executar o executor de loop diretamente usando:

    ./python.sh exts/isaacsim.cortex.framework/omni/isaac/cortex/cortex_main.py \
        --usd_env=Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd

Terminal 2: Ativar comportamento.
    cd standalone_examples/cortex
    ./cortex activate build_block_tower.py

# Ele inicia o executor do comportamento de empilhamento de blocos. 
# A qualquer momento, podemos alternar os comportamentos.

    ./cortex activate go_home.py 
# Envia o robô para a posição inicial e permite o controle manual usando o prim de destino.

    ./cortex activate reset_world.py 
# Redefine os blocos para a posição inicial.
```
Neste exemplo, você pode interagir com os blocos enquanto eles tentam construir a torre e o robô reagirá.

## Iniciando o sistema com os robôs belief e sim

Executando os robôs belief e sim. Esta configuração é semelhante, exceto que usa um
arquivo de ambiente USD diferente, e você precisa executar o controlador simulado
a partir de `cortex_control` para conectar o robô sim ao robô belief que toma decisões.
```
Terminal 1: Iniciar um roscore

Terminal 2: Iniciar o executor de loop do córtex passando o ambiente USD do mundo dos blocos e usando --enable_ros.
cd standalone_examples/cortex
./cortex launch \
    --usd_env=Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief_sim.usd \
    --enable_ros

Terminal 3: Ativar comportamento.

cd standalone_examples/cortex
./cortex activate build_block_tower.py

# Neste ponto, o robô de crença começará a tentar pegar o primeiro bloco, mas o robô simulador não está seguindo porque o controlador não está em execução. Precisamos iniciar o controlador.

Terminal 4: Iniciar o controlador simulado

rosrun cortex_control sim_controller
```

# Conectando a um robô físico

O robô físico substituirá o robô simulado e executaremos um controlador do mundo real em vez do controlador simulado. Aqui, mostraremos como enviar o robô para casa e usar o controle manual, caso contrário, você precisaria de um módulo de percepção do mundo real.

Inicie o sistema apenas com a crença. Este é o mesmo procedimento descrito acima.
```
Terminal 1: Iniciar um roscore

Terminal 2: Iniciar o executor de loop do córtex passando o ambiente USD do mundo dos blocos.

cd standalone_examples/cortex
./cortex launch \
--usd_env=Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd \
--enable_ros
```
Neste ponto, podemos executar os comportamentos como antes, mas o sistema executará apenas o robô de crença simulado. O robô físico ainda não está conectado.

Agora, inicie o robô Franka e os controladores `cortex_control_franka`. No ponto em que iniciamos o controlador de posição conjunta no terminal 3 abaixo, você deverá ver o robô de crença córtex simulado sincronizar com o robô físico. Ele acionará o robô nesse ponto, então você poderá ver algum leve movimento, mas não deve ser muito. Certifique-se de ter a parada de emergência pronta caso algo dê errado.
```
Terminal 1: Iniciar o gerenciador do controlador Franka

source ~/catkin_ws/devel/setup.bash
roslaunch cortex_control_franka franka_control_lula.launch

Terminal 2: Definir limites de torque alto para Franka

rosrun cortex_control_franka set_high_collision_thresholds

Terminal 3: Inicializar o controlador de posição — iniciar este controlador sincroniza a crença com o robô físico.

roslaunch cortex_control_franka joint_position_controller.launch

Terminal 4: Iniciar o ouvinte do comando do gripper

rosrun cortex_control_franka franka_gripper_command_relay.py
```

Neste ponto, podemos executar alguns comportamentos e veremos o robô físico seguindo o robô simulado. Tente o seguinte:
```
cd standalone_examples/cortex
./cortex activate open_gripper.py   # Abre o gripper físico
```
Selecione o prim e, em seguida, selecione a ferramenta "Mover" na barra de ferramentas ao longo da borda esquerda da janela de visualização.
Em seguida, arraste as setas.

# Convenções de configuração de mundos

Os mundos do Cortex USD seguem uma convenção específica de nomenclatura de caminhos. Bons exemplos são:
```
Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd
Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief_sim.usd
Isaac/Samples/Cortex/UR10/Basic/cortex_ur10_basic_belief.usd
Isaac/Samples/Cortex/UR10/Basic/cortex_ur10_basic_belief_sim.usd
```

Assume-se que esses ambientes sejam configurados em centímetros.

O ambiente de crença é adicionado ao caminho `/cortex/belief` e o ambiente de sim (se existir) usado é adicionado ao caminho `/cortex/sim`. Cada um desses ambientes contém os subprims `robot` e `objects`. O robô deve ter um atributo de metadados de string `cortex:robot_type` informando ao sistema o tipo de robô.
Os valores atualmente suportados são `cortex:robot_type = {'franka', 'ur10'}`. Além disso, objetos adicionados à cena podem ter um atributo opcional `cortex:is_obstacle` que, quando definido como True, carrega o objeto como um obstáculo. Isso é usado no exemplo de empilhamento de blocos para que a torre se torne um obstáculo automaticamente ao ser criada. Os objetos não precisam ter um atributo `cortex:is_obstacle`. Se um não estiver presente, presume-se que o objeto não seja um obstáculo.

Todos os prims xform que representam robôs e objetos devem seguir as convenções USD da especificação de transformação da API principal do Isaac Sim. Especificamente, eles devem ter atributos `Transform` especificados por
`xformOp:translate`, `xformOp:orient`, `xformOp:scale` com `xformOpOrder` fornecido como `[xformOp:translate, xformOp:orient, xformOp:scale]`.

Por exemplo, o ambiente de empilhamento de blocos contendo `belief` e `sim` é apresentado como:
```
/cortex
/belief
/robot          # Franka USD com cortex:robot_type de 'franka'
/objects
/red_block      # cortex:is_obstacle = True
/yellow_block   # cortex:is_obstacle = True
/green_block    # cortex:is_obstacle = Trueexe
/green_block
/blue_block

```
Muitas vezes, é útil configurar um ambiente comum que seja compartilhado por `/cortex/belief` e `/cortex/sim`. Isso facilita a configuração das variantes belief-only e belief-sim do ambiente USD.

Outros atributos e prims
- O robô belief possui `cortex:adaptive_cycle_dt` (Double) e `cortex:is_suppressed` (Bool). Eles são usados ​​internamente pelo Cortex e serão adicionados automaticamente na inicialização. Não há problema se o ambiente USD já os tiver.
- Prim `/cortex/belief/motion_controller_target`. Este é um prim de cubo simples usado para controlar manualmente o robô. Se já estiver no ambiente, o Cortex o usará. Caso contrário, ele criará o seu próprio ao inicializar o Motion Commander.

# Detalhamento de arquivos

Executor de loop principal do Cortex: Aplicativo Python autônomo que executa o executor de loop principal do Cortex e inicia as extensões
`cortex_{ros,sim}`.
- `cortex_main.py`: Ponto de entrada primário e executor de loop principal do Cortex. Este executa o aplicativo Python autônomo principal do Cortex. Ele aponta para seu próprio arquivo de experiência, que inclui a extensão isaacsim.cortex.framework.
Um ambiente USD compatível com o Cortex é passado por meio de uma flag. Ele inicia automaticamente as extensões
`cortex_ros` e `cortex_sim`. O primeiro está sempre em execução, portanto, um robô físico pode ser
conectado a qualquer momento. Se o ambiente USD tiver um ambiente Sim, esse robô será usado no lugar de um
robô físico.

Extensões: Extensões carregadas na inicialização, transferindo a comunicação ROS para o robô físico e o
robô simulado.

- `cortex_ros.py`: Gerencia conexões ROS para obter informações perceptuais no córtex e enviar
informações de controle para fora do córtex.
- `cortex_sim.py`: Gerencia a criação da interface de comunicação ROS para imitar um robô físico usando
um ambiente simulado.

Estrutura de decisão: A estrutura de decisão principal
- `df.py`: Ferramentas da estrutura principal, incluindo uma implementação de redes decisoras e máquinas de
estado.
- `dfb.py`: Comportamentos da estrutura de decisão úteis em vários scripts de comportamento. Estes incluem
tipos e ações específicas de nós decisores.
- `df_behavior_watcher.py`: Monitora o arquivo `df_behavior_module.py` em busca de alterações. Recarrega
quando uma alteração é detectada.
- `df_behavior_module.py`: Este arquivo é constantemente monitorado pelo principal executor do loop do córtex. Quando
ele muda, o comportamento é carregado e executado. Na inicialização, nada é executado até que um comportamento seja
explicitamente ativado.

Diretório `standalone_examples/cortex`: Contém exemplos de scripts de comportamento definidos pelo usuário.
- `activate`: script simples para copiar um comportamento para o `df_behavior_module.py` monitorado no
diretório principal do córtex para ativá-lo. `df_behavior_module.py` é monitorado pelo observador de comportamento
em `df_behavior_watcher.py`.
- `clear`: limpa o comportamento atual. O robô não executará nenhum comportamento, podendo ser controlado
manualmente após isso, movendo o prim `motion_controller_target`.
- `go_home.py`: Envia o robô para a posição inicial. Assim que o robô chegar à posição inicial,
ele pode ser controlado usando o prim `motion_controller_target`.
- `manual_control.py`: Define o robô para controle manual. O robô pode ser controlado movendo o prim `motion_controller_target`. Este é um comportamento específico que não faz nada (ao contrário de nenhum comportamento
como em `clear`).
- `reset_world.py`: redefine os objetos nos ambientes de crença e simulação de volta às suas
configurações iniciais.
- comportamentos específicos de franka dentro de `behaviors/franka`
- `build_block_tower.py`: constrói uma torre de blocos no mundo dos blocos. Este comportamento é reativo a
mudanças inesperadas nos blocos/torre.
- `block_tower_monitors.py`: inicia apenas os monitores da torre de blocos.
- `send_blocks_to_tower.py`: envia os blocos para a torre de destino correta.
- `send_blocks_to_bad_tower.py`: envia o bloco para uma torre ruim, onde o robô terá que
demolir e reconstruir a torre correta.
- `open_gripper.py`: abre a garra.
- `close_gripper.py`: Fecha a pinça.

Ferramentas do Cortex:
- `cortex_utils.py`: Utilitários para configurar o Cortex.

- `cortex_object.py`: Uma representação de objeto que envolve objetos da API principal que simplifica o acesso e o uso dos atributos do Cortex. Por exemplo, objetos do Cortex têm poses medidas gravadas no
USD. O objeto do Cortex possui APIs para ler essa pose medida e sincronizar a pose do objeto (crença)
com essa pose medida.

- `motion_commander.py`: Um wrapper em torno das políticas de movimento inteligentes de Isaac Sim, fornecendo uma interface de API de comando com um alvo de pose e a direção de aproximação correspondente. Fornece métodos convenientes para acessar a cinemática direta ao quadro de controle e abrir e fechar a pinça.

Além disso, suaviza automaticamente os comandos enviados ao comandante usando `smoothed_command.py` e usa
o `RmpFlowSmoothed` para tornar os movimentos resultantes seguros para execução no robô real.

- `smoothed_command.py`: Uma ferramenta para suavizar comandos automaticamente.

- `synchronized_time.py`: Um utilitário ROS usado para implementar o protocolo de sincronização de relógio com o controlador para se adaptar a velocidades de relógio ligeiramente diferentes entre o controlador do robô embarcado e o córtex da máquina em execução. (Por exemplo, o relógio do controlador Franka às vezes corre um pouco mais rápido, fazendo com que o interpolador do controlador ultrapasse o buffer ao longo do tempo. Este protocolo de sincronização permite o monitoramento constante do delta de tempo para permitir execuções contínuas de longo prazo no robô físico.)


utils:
- `cli.py`: Ferramentas simples para configurar interfaces de linha de comando convenientes. Usado especialmente em alguns dos testes.

- `gf_conversions.py`: Ferramentas para facilitar a leitura de informações de e para USD através da interface Gf.
- `math_util.py`: Ferramentas e utilitários matemáticos.

-- `ros_tf_util.py`: utilitários baseados em ROS.

- `tools.py`: utilitários comuns para executar loops estáveis ​​e criação de perfil.

testes:
- `tests/test_df.py`: testes unitários para o framework de decisão (df.py).

- `tests/test_motion_commander.py`: um aplicativo Python independente que inicia o Motion Commander em um ambiente Franka básico para testar e demonstrar a interface do Motion Commander.



# Detalhes

## Construindo

`cortex_control` e `cortex_control_franka` estão localizados em `ros_workspace/src`. 
Siga as instruções para construir esse espaço de trabalho ROS. 
Você também pode copiá-los ou criar um link simbólico para um espaço de trabalho ROS separado. `cortex_contro_franka` depende de `cortex_control` e `franka_ros`, mas `cortex_control` é independente e `franka_ros` já deve estar instalado com a distribuição ROS. Caso contrário, você pode encontrá-lo no site da Franka.

Ao testar essas ferramentas em simulação, você precisa apenas da biblioteca `cortex_control` (que contém o binário `sim_controller`). No entanto, para controlar o robô físico, você precisa instalar `cortex_control` e `cortex_control_franka` em um ambiente de trabalho catkin na máquina de controle em tempo real da Franka.

Construa o ambiente de trabalho catkin.
```
cd ~/catkin_ws
catkin_make
```

# Solução de Problemas

Ao reiniciar o controlador do robô físico, é melhor desativar todo o gerenciador do controlador (ou seja, tudo na máquina de tempo real) e reiniciar tudo.
