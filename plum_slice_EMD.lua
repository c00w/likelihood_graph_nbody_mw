---~/Dropbox/Repos/milkywayathome_client/bin/milkyway_nbody -f ./plum_slice_model_good.lua -e 1 -o run_out -z output.hist  2 2 4 0.5 10 .20

arg = { ... }

assert(#arg == 6, "Expected 6 arguments")
assert(argSeed ~= nil, "Expected seed")

prng = DSFMT.create(argSeed)

evolveTime       = arg[1]
reverseOrbitTime = arg[2]

r0  = arg[3]
light_r_ratio = arg[4]

dwarfMass  = arg[5]
light_mass_ratio = arg[6]

model1Bodies = 100000
totalBodies = model1Bodies

nbodyLikelihoodMethod = "EMD"
nbodyMinVersion = "0.80"

function makePotential()
   return  Potential.create{
      spherical = Spherical.spherical{ mass  = 1.52954402e5, scale = 0.7 },
      disk      = Disk.miyamotoNagai{ mass = 4.45865888e5, scaleLength = 6.5, scaleHeight = 0.26 },
      halo      = Halo.logarithmic{ vhalo = 73, scaleLength = 12.0, flattenZ = 1.0 }
   }
end


encMass = plummerTimestepIntegral(r0*light_r_ratio, r0 , dwarfMass, 1e-7)

-- This is also required
function makeContext()
   return NBodyCtx.create{
      timeEvolve = evolveTime,
      timestep   = sqr(1/10.0) * sqrt((pi_4_3 * cube(r0)) / (encMass + dwarfMass)),
      eps2       = calculateEps2(totalBodies, r0),
      criterion  = "NewCriterion",
      useQuad    = true,
      theta      = 1.0
   }
end

-- Also required
function makeBodies(ctx, potential)
    local firstModel
    local finalPosition, finalVelocity = reverseOrbit{
        potential = potential,
        position  = lbrToCartesian(ctx, Vector.create(218, 53.5, 28.6)),
        velocity  = Vector.create(-156, 79, 107),
        tstop     = reverseOrbitTime,
        dt        = ctx.timestep / 10.0
    }

    firstModel = predefinedModels.plummer{
        nbody       = model1Bodies,
        prng        = prng,
        position    = finalPosition,
        velocity    = finalVelocity,
        mass        = dwarfMass ,
        scaleRadius = r0,
        ignore      = true
    }


    for i,v in ipairs(firstModel) 
    do 
       --Figure out properties
       r_2 = (finalPosition.x - v.position.x)^2 + (finalPosition.y - v.position.y)^2 + (finalPosition.z - v.position.z)^2
       r = r_2 ^ (0.5)
       mass_enclosed = dwarfMass * r^2 * r0^2 * ((r^2 + r0^2)^(-2.5))

       --Get light sphere properties
       light_dwarfMass = dwarfMass * light_mass_ratio
       light_r0 = r0 * light_r_ratio
       light_mass_enclosed = light_dwarfMass * r^2 * light_r0^2 * ((r^2 + light_r0^2)^(-2.5))

       --Chance object is light_mass = light/dwarf
       chance = light_mass_enclosed/ mass_enclosed
       
       ---Do random calculation
        if(prng:random() < chance)
        then
            v.ignore=false
        end

    end

    ---Check that mass is rightish
    mass = 0
    count_light = 0
    for i,v in ipairs(firstModel) 
    do 
        if (v.ignore == false)
        then
            count_light = count_light +1
            mass = mass + dwarfMass / totalBodies
        end
    end

    ---See if its bigger than the mass epsilon
    if( dwarfMass * light_mass_ratio - mass >= dwarfMass/totalBodies )
    then
        --- Figure out how many bodies we should add
        missing_mass = dwarfMass * light_mass_ratio - mass
        bodies_needed = missing_mass / (dwarfMass / totalBodies)

        --- Figure out what the odds should be to produce that distribution
        chance = bodies_needed / (totalBodies - count_light)


        --- sanity checks
        if(chance < 0)
        then
            chance = 0
        end

        if( chance > 1)
        then
            chance = 1
        end

        ---Loop through adding bodies with chance of chance
        for i,v in ipairs(firstModel)
        do  
            ---Do random calculation
            if(prng:random() < chance)
            then
                v.ignore=false
            end
        end
    end

   return firstModel
end

function makeHistogram()
   return HistogramParams.create()
end


