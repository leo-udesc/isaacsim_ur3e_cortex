Este exemplo autônomo fornece um script genérico para executar um exemplo de follow-target em qualquer robô suportado que use o RMPflow para atingir um alvo enquanto evita obstáculos. O propósito deste script é mostrar apenas como usar o RMPflow e, para simplificar, ele não usa o paradigma de tarefa/controlador que é típico em outros exemplos do Isaac Sim.

O script ./supported_robot_follow_target_example.py recebe em tempo de execução o caminho para o ativo USD do robô (que é assumido como armazenado no Nucleus Server) e o nome do robô. Ao executar o script com os argumentos de linha de comando padrão, a lista de nomes de robôs suportados será impressa no terminal.

###### Command Line Arguments

Os argumentos para os command-line arguments são:

    -v,--verbose: Se True, imprime informações úteis de tempo de execução, como a lista de nomes de robôs suportados que mapeiam para arquivos de configuração do RMPflow. O padrão é 'True'

    --robot-name: Name of robot that maps to the stored RMPflow config.  Defaults to "Cobotta_Pro_900"

    --usd-path: Caminho para o ativo USD do robô no Nucleus Server.  O padrão para
                "/Isaac/Robots/Denso/cobotta_pro_900.usd".  
                A localização típica de um robô específico está em
                "/Isaac/Robots/{manufacturer_name}/{robot_name}/{robot_name}.usd"
                
    --add-orientation-target: Adicione a orientação do cubo de destino ao destino do RMPflow. O padrão é False.


###### Choosing Correct Robot Name Argument
Com os argumentos padrão, o script acima será executado usando o robô Cobotta Pro 900 e produzirá a seguinte saída:

Nomes de robôs suportados com configuração RMPflow fornecida
        ['Franka', 'UR3', 'UR3e', 'UR5', 'UR5e', 'UR10', 'UR10e', 'UR16e', 'Rizon4', 'Cobotta_Pro_900', 'Cobotta_Pro_1300', 'RS007L', 'RS007N', 'RS013N', 'RS025N', 'RS080N', 'FestoCobot']

    Configuração RMPflow referenciada com sucesso para Cobotta_Pro_900. Usando os seguintes parâmetros para inicializar a classe RmpFlow:
    {
        'end_effector_frame_name': 'gripper_center',
        'ignore_robot_state_updates': False,
        'maximum_substep_size': 0.00334,
        'rmpflow_config_path': '/path/to/omni_isaac_sim/_build/linux-x86_64/release/exts/isaacsim.robot_motion.motion_generation/motion_policy_configs/./Denso/cobotta_pro_900/rmpflow/cobotta_rmpflow_common.yaml',
        'robot_description_path': '/path/to/omni_isaac_sim/_build/linux-x86_64/release/exts/isaacsim.robot_motion.motion_generation/motion_policy_configs/./Denso/cobotta_pro_900/rmpflow/robot_descriptor.yaml',
        'urdf_path': '/path/to/omni_isaac_sim/_build/linux-x86_64/release/exts/isaacsim.robot_motion.motion_generation/motion_policy_configs/./Denso/cobotta_pro_900/rmpflow/../cobotta_pro_900_gripper_frame.urdf'
    }

Os nomes dos robôs suportados são adequados para o argumento `--robot-name`, e cada um deve corresponder corretamente ao caminho USD do robô. Em uma versão futura, os dados de configuração para robôs suportados serão centralizados de forma que apenas um único argumento será necessário. O método específico de acessar as configurações RMPflow do robô suportado fornecido aqui será então descontinuado.

A saída restante mostra as informações de configuração do RMPflow que são encontradas sob o nome "Cobotta_Pro_900". Esta configuração é usada para inicializar a classe `RmpFlow`.


###### Examples of loading other robots

Várias combinações válidas de argumentos de linha de comando são mostradas para diferentes robôs suportados:

    python.sh supported_robot_follow_target_example.py --robot-name RS080N --usd-path "/Isaac/Robots/Kawasaki/RS080N/rs080n_onrobot_rg2.usd"

    python.sh supported_robot_follow_target_example.py --robot-name UR16e --usd-path "/Isaac/Robots/UniversalRobots/ur16e/ur16e.usd"

    python.sh supported_robot_follow_target_example.py --robot-name FestoCobot --usd-path "/Isaac/Robots/Festo/FestoCobot/festo_cobot.usd"


