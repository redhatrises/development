documentation_complete: true
title: Java Runtime Environment (JRE) STIG
title_override: true
profile_id: stig-java-upstream
extends: test

description: |
    The Java Runtime Environment (JRE) is a bundle developed
    and offered by Oracle Corporation which includes the Java Virtual Machine
    (JVM), class libraries, and other components necessary to run Java
    applications and applets. Certain default settings within the JRE pose
    a security risk so it is necessary to deploy system wide properties to
    ensure a higher degree of security when utilizing the JRE.

    The IBM Corporation also develops and bundles the Java Runtime Environment
    (JRE) as well as Red Hat with OpenJDK.

rule_selection:
    - rule: java_jre_deployment_config_exists
      selected: true
    - rule: java_jre_deployment_config_properties
    - rule: java_jre_updated

rule_configuration:
    - item: login_banner_text
      selector: usgcb_default

