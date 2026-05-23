MODULE IoT_Move

    ! ------------------------------------------------------------
    ! offset{1} = World/WObj X offset in mm from startup pose
    ! offset{2} = World/WObj Y offset in mm from startup pose
    ! offset{3} = World/WObj Z offset in mm from startup pose
    ! offset{4} = Rx rotation in degrees from startup orientation
    ! offset{5} = Ry rotation in degrees from startup orientation
    ! offset{6} = Rz rotation in degrees from startup orientation
    !--------------------------------------------------------------

    PERS num offset{6}:=[100,0,0,0,0,0];
    
    PERS string robotName:="Robot_1";
    PERS num robotID:=1;
    
    ! Python sets this TRUE whenever it writes a new command
    PERS bool moveRequest:=FALSE;

    ! Feedback for Python readback
    PERS bool moveDone:=FALSE;

    ! Status:
    !  0 = idle
    !  1 = filtering / moving
    !  2 = reached filtered target
    ! -1 = error / rejected
    PERS num moveStatus:=1;

    CONST num POS_EPS_MM := 0.5;
    CONST num ROT_EPS_DEG := 0.2;


    ! ------------------------------------------------------------
    ! Runtime startup target
    ! ------------------------------------------------------------
    ! This is captured once when RAPID starts.
    !
    ! The robot target is:
    !     position    = startup position + filtered world offset
    !     orientation = startup orientation + filtered rotation offset
    !
    ! The dummy value below is overwritten by CRobT() in main().
    ! ------------------------------------------------------------

    PERS robtarget startup_target := [
        [511.005,69.7674,594],
        [0.5,-3.2865E-8,0.866025,-6.15193E-8],
        [0,-1,0,0],
        [9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]
    ];

    VAR robtarget target_next;

    VAR pose startup_pose;
    VAR pose rot_offset_pose;
    VAR pose final_rot_pose;


    ! ------------------------------------------------------------
    ! Low-pass filter variables
    ! ------------------------------------------------------------

    PERS num targetOffset{6}:=[100,0,0,0,0,0];
    PERS num filteredOffset{6}:=[25,0,0,0,0,0];

    CONST num LPF_ALPHA := 0.25;


    PROC main()

        TPWrite "IoT Gateway control started.";

        moveRequest:=FALSE;
        moveDone:=TRUE;
        moveStatus:=2;

        ConfL \Off;

        ! ------------------------------------------------------------
        ! Capture robot pose ONCE at program start.
        ! All future offsets are relative to this pose.
        ! ------------------------------------------------------------

        startup_target := CRobT(\Tool:=tool0 \WObj:=wobj0);

        TPWrite "Startup pose captured:";
        TPWrite NumToStr(startup_target.trans.x, 2);
        TPWrite NumToStr(startup_target.trans.y, 2);
        TPWrite NumToStr(startup_target.trans.z, 2);

        ! Initialize filter at zero offset
        targetOffset := [0,0,0,0,0,0];
        filteredOffset := [0,0,0,0,0,0];

        WHILE TRUE DO

            ! ------------------------------------------------------------
            ! Waits for IoT gateway to writ variable
            ! ------------------------------------------------------------

            IF moveRequest THEN

                TPWrite "New target offset received.";

                targetOffset{1}:=offset{1};
                targetOffset{2}:=offset{2};
                targetOffset{3}:=offset{3};
                targetOffset{4}:=offset{4};
                targetOffset{5}:=offset{5};
                targetOffset{6}:=offset{6};

                moveStatus:=1;
                moveDone:=FALSE;

                TPWrite "Accepted offset command:";
                TPWrite NumToStr(targetOffset{1}, 2);
                TPWrite NumToStr(targetOffset{2}, 2);
                TPWrite NumToStr(targetOffset{3}, 2);

                ! Resetting only the request flag.
            ENDIF

            ! ------------------------------------------------------------
            ! Low-pass filter
            ! ------------------------------------------------------------

            filteredOffset{1}:=filteredOffset{1} + LPF_ALPHA * (targetOffset{1} - filteredOffset{1});
            filteredOffset{2}:=filteredOffset{2} + LPF_ALPHA * (targetOffset{2} - filteredOffset{2});
            filteredOffset{3}:=filteredOffset{3} + LPF_ALPHA * (targetOffset{3} - filteredOffset{3});
            filteredOffset{4}:=filteredOffset{4} + LPF_ALPHA * (targetOffset{4} - filteredOffset{4});
            filteredOffset{5}:=filteredOffset{5} + LPF_ALPHA * (targetOffset{5} - filteredOffset{5});
            filteredOffset{6}:=filteredOffset{6} + LPF_ALPHA * (targetOffset{6} - filteredOffset{6});


            ! ------------------------------------------------------------
            ! Translation
            ! ------------------------------------------------------------
            target_next := startup_target;

            target_next.trans.x := startup_target.trans.x + filteredOffset{1};
            target_next.trans.y := startup_target.trans.y + filteredOffset{2};
            target_next.trans.z := startup_target.trans.z + filteredOffset{3};


            ! ------------------------------------------------------------
            ! Rotation
            ! ------------------------------------------------------------
            startup_pose.trans := [0,0,0];
            startup_pose.rot := startup_target.rot;

            rot_offset_pose.trans := [0,0,0];
            rot_offset_pose.rot := OrientZYX(
                filteredOffset{6},
                filteredOffset{5},
                filteredOffset{4}
            );

            final_rot_pose := PoseMult(startup_pose, rot_offset_pose);

            target_next.rot := final_rot_pose.rot;

            target_next.robconf := startup_target.robconf;
            target_next.extax := startup_target.extax;

            ! ------------------------------------------------------------
            ! Execute  motion
            ! ------------------------------------------------------------

            MoveL target_next, v20, z1, tool0\WObj:=wobj0;


            ! ------------------------------------------------------------
            ! Check whether filtered offset has reached target offset
            ! ------------------------------------------------------------

            IF Abs(targetOffset{1} - filteredOffset{1}) < POS_EPS_MM AND
               Abs(targetOffset{2} - filteredOffset{2}) < POS_EPS_MM AND
               Abs(targetOffset{3} - filteredOffset{3}) < POS_EPS_MM AND
               Abs(targetOffset{4} - filteredOffset{4}) < ROT_EPS_DEG AND
               Abs(targetOffset{5} - filteredOffset{5}) < ROT_EPS_DEG AND
               Abs(targetOffset{6} - filteredOffset{6}) < ROT_EPS_DEG THEN

                moveStatus:=2;
                moveDone:=TRUE;
                moveRequest:=FALSE;

            ELSE

                moveStatus:=1;
                moveDone:=FALSE;
                

            ENDIF


            WaitTime 0.02;

        ENDWHILE


    ERROR

        moveRequest:=FALSE;
        moveDone:=FALSE;
        moveStatus:=-1;

        TPWrite "RAPID error during filtered world offset move.";
        TPWrite "ERRNO:";
        TPWrite NumToStr(ERRNO, 0);

    ENDPROC

ENDMODULE