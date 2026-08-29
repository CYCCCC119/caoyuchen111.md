-- =============================================================
-- 重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统
-- 业务数据库初始化脚本（MySQL 8.0）
-- 用途：建库建表 + 基础业务数据导入，支撑系统业务流程跑通
-- 默认密码：所有演示账号密码均为 123456（MD5 已加密存储）
-- =============================================================

CREATE DATABASE IF NOT EXISTS tightening_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE tightening_db;

-- -------------------------------------------------------------
-- 1. 螺栓基础信息表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS bolt_info;
CREATE TABLE bolt_info (
    id            INT AUTO_INCREMENT PRIMARY KEY COMMENT '螺栓ID',
    spec          VARCHAR(16)  NOT NULL COMMENT '螺栓规格（M12/M16/M20/M24）',
    grade         VARCHAR(8)   NOT NULL COMMENT '性能等级（8.8/10.9/12.9）',
    standard_torque DECIMAL(8,2) NOT NULL COMMENT '标准拧紧扭矩(N·m)',
    material      VARCHAR(32)  DEFAULT NULL COMMENT '材质',
    remark        VARCHAR(255) DEFAULT NULL COMMENT '备注'
) ENGINE=InnoDB COMMENT='螺栓基础信息表';

-- -------------------------------------------------------------
-- 2. 工位信息表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS workstation;
CREATE TABLE workstation (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '工位ID',
    name        VARCHAR(64) NOT NULL COMMENT '工位名称',
    device_no   VARCHAR(32) NOT NULL COMMENT '设备编号',
    owner       VARCHAR(32) DEFAULT NULL COMMENT '负责人',
    workshop    VARCHAR(64) DEFAULT NULL COMMENT '所属车间'
) ENGINE=InnoDB COMMENT='工位信息表';

-- -------------------------------------------------------------
-- 3. 工艺参数表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS process_param;
CREATE TABLE process_param (
    id           INT AUTO_INCREMENT PRIMARY KEY COMMENT '参数ID',
    spec         VARCHAR(16) NOT NULL COMMENT '螺栓规格',
    target_torque DECIMAL(8,2) NOT NULL COMMENT '目标扭矩(N·m)',
    speed        DECIMAL(8,2) NOT NULL COMMENT '拧紧转速(deg/s)',
    feed         DECIMAL(8,2) NOT NULL COMMENT '进给量(mm)',
    version      VARCHAR(16) NOT NULL COMMENT '版本号',
    status       TINYINT DEFAULT 1 COMMENT '1=启用 0=停用'
) ENGINE=InnoDB COMMENT='工艺参数表';

-- -------------------------------------------------------------
-- 4. 拧紧记录表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS tightening_record;
CREATE TABLE tightening_record (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    bolt_id        INT NOT NULL COMMENT '螺栓ID',
    workstation_id INT NOT NULL COMMENT '工位ID',
    operator       VARCHAR(32) DEFAULT NULL COMMENT '操作人员',
    record_time    DATETIME NOT NULL COMMENT '拧紧时间',
    quality_label  TINYINT NOT NULL COMMENT '质量标签 0合格 1欠拧 2过拧 3滑牙 4虚拧',
    confidence     DECIMAL(5,4) DEFAULT NULL COMMENT '判定置信度',
    feature_json   JSON DEFAULT NULL COMMENT '特征向量(JSON)',
    CONSTRAINT fk_record_bolt FOREIGN KEY (bolt_id) REFERENCES bolt_info(id),
    CONSTRAINT fk_record_ws   FOREIGN KEY (workstation_id) REFERENCES workstation(id)
) ENGINE=InnoDB COMMENT='拧紧记录表';

-- -------------------------------------------------------------
-- 5. 质量预警表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS quality_warning;
CREATE TABLE quality_warning (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '预警ID',
    record_id   BIGINT NOT NULL COMMENT '关联拧紧记录ID',
    defect_type TINYINT NOT NULL COMMENT '缺陷类型',
    level       TINYINT NOT NULL COMMENT '预警级别 1轻微 2一般 3严重',
    status      TINYINT DEFAULT 0 COMMENT '处理状态 0未处理 1已处理',
    create_time DATETIME NOT NULL COMMENT '创建时间',
    CONSTRAINT fk_warning_record FOREIGN KEY (record_id) REFERENCES tightening_record(id)
) ENGINE=InnoDB COMMENT='质量预警表';

-- -------------------------------------------------------------
-- 6. 用户表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS user_info;
CREATE TABLE user_info (
    id           INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username     VARCHAR(32) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(64) NOT NULL COMMENT '密码哈希',
    role         VARCHAR(32) NOT NULL COMMENT '角色：operator/inspector/engineer/admin',
    real_name    VARCHAR(32) DEFAULT NULL COMMENT '姓名'
) ENGINE=InnoDB COMMENT='用户表';

-- =============================================================
-- 基础数据导入
-- =============================================================

INSERT INTO bolt_info (spec, grade, standard_torque, material) VALUES
('M12', '8.8',  80.00, '碳钢'),
('M12', '10.9', 80.00, '合金钢'),
('M16', '8.8', 180.00, '碳钢'),
('M16', '10.9',180.00, '合金钢'),
('M20', '8.8', 320.00, '碳钢'),
('M20', '12.9',320.00, '合金钢'),
('M24', '8.8', 520.00, '碳钢'),
('M24', '12.9',520.00, '合金钢');

INSERT INTO workstation (name, device_no, owner, workshop) VALUES
('一号装配工位', 'WS-001', '张伟', '总装一车间'),
('二号装配工位', 'WS-002', '李强', '总装一车间'),
('三号装配工位', 'WS-003', '王芳', '总装二车间'),
('四号装配工位', 'WS-004', '刘洋', '总装二车间');

INSERT INTO process_param (spec, target_torque, speed, feed, version, status) VALUES
('M12',  80.00, 150.00, 2.0, 'V1.0', 1),
('M16', 180.00, 140.00, 2.5, 'V1.0', 1),
('M20', 320.00, 130.00, 3.0, 'V1.0', 1),
('M24', 520.00, 120.00, 3.5, 'V1.0', 1);

INSERT INTO user_info (username, password_hash, role, real_name) VALUES
('operator',  'e10adc3949ba59abbe56e057f20f883e', 'operator',  '张伟'),
('inspector', 'e10adc3949ba59abbe56e057f20f883e', 'inspector', '李强'),
('engineer',  'e10adc3949ba59abbe56e057f20f883e', 'engineer',  '王芳'),
('admin',     'e10adc3949ba59abbe56e057f20f883e', 'admin',     '刘洋');
