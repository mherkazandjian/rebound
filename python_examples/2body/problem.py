# Import the rebound module
import rebound
import numpy as np
from rebound.interruptible_pool import InterruptiblePool


torb = 2.*np.pi
tmax = 1000.34476128*torb

def simulation(par):
    anom, dt, e, integrator = par

    e = 1.-pow(10.,e)
    dt = pow(10.,dt)*torb

    rebound.reset()
    rebound.set_integrator(integrator)
    rebound.set_force_is_velocitydependent(0)
    rebound.set_dt(dt)

    rebound.add_particle(m=1.)
    rebound.add_particle(m=0., x=(1.-e), vy=np.sqrt((1.+e)/(1.-e)))
    particles = rebound.get_particles()
    
    Ei = -1./np.sqrt(particles[1].x*particles[1].x+particles[1].y*particles[1].y+particles[1].z*particles[1].z) + 0.5 * (particles[1].vx*particles[1].vx+particles[1].vy*particles[1].vy+particles[1].vz*particles[1].vz)

    rebound.integrate(tmax,exactFinishTime=0,keepSynchronized=1)
    
    Ef = -1./np.sqrt(particles[1].x*particles[1].x+particles[1].y*particles[1].y+particles[1].z*particles[1].z) + 0.5 * (particles[1].vx*particles[1].vx+particles[1].vy*particles[1].vy+particles[1].vz*particles[1].vz)

    return [float(rebound.get_iter())/rebound.get_t()*dt, np.fabs((Ef-Ei)/Ei)+1e-16, rebound.get_timing()/rebound.get_t()*dt*1e6/2., (Ef-Ei)/Ei]


N = 200
dts = np.linspace(-3,-0.1,N)
e0s = np.linspace(0,-10,N)
integrators= ["wh","mikkola"]

niter = []
energyerror = []
energyerror_sign = []
timing = []

for integrator in integrators:
    print("Running "+ integrator)
    parameters = [(1.732, dts[i], e0s[j], integrator) for j in range(N) for i in range(N)]

    pool = InterruptiblePool(12)
    res = pool.map(simulation,parameters)
    res = np.nan_to_num(res)
    niter.append(res[:,0].reshape((N,N)))
    energyerror.append(res[:,1].reshape((N,N)))
    timing.append(res[:,2].reshape((N,N)))
    energyerror_sign.append(res[:,3].reshape((N,N)))

import matplotlib; matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.colors import LogNorm

f,axarr = plt.subplots(3,2,figsize=(17,12))
extent=[dts.min(), dts.max(), e0s.max(), e0s.min()]
plt.subplots_adjust(wspace = 0.4)

for ay in axarr:
    for ax in ay:
        # ax = axarr
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel(r"log10$(dt/t_{orb})$")
        ax.set_ylabel(r"log10$(1-e)$")

for i, integrator in enumerate(integrators):
    im1 = axarr[0,i].imshow(energyerror[i], norm=LogNorm(), vmax=np.max(energyerror), vmin=1e-16, aspect='auto', origin="lower", interpolation='nearest', cmap="RdYlGn_r", extent=extent)
    cb1 = plt.colorbar(im1, ax=axarr[0,i])
    cb1.solids.set_rasterized(True)
    cb1.set_label("Relative energy error, " +integrator)
    
    im2 = axarr[1,i].imshow(np.sign(energyerror_sign[i]), vmax=1, vmin=-1, aspect='auto', origin="lower", interpolation='nearest', cmap="bwr", extent=extent)
    cb2 = plt.colorbar(im2, ax=axarr[1,i])
    cb2.solids.set_rasterized(True)
    t = ticker.MaxNLocator(nbins=3)
    cb2.locator = t
    cb2.update_ticks()
    cb2.set_label("Sign of energy error, " +integrator)

    im3 = axarr[2,i].imshow(timing[i], vmin=0., vmax=3.*np.median(timing), aspect='auto', origin="lower", interpolation="nearest", cmap="RdYlGn_r", extent=extent)
    cb3 = plt.colorbar(im3, ax=axarr[2,i])
    cb3.solids.set_rasterized(True)
    cb3.set_label("Runtime per timestep [$\mu$s], " +integrator)
    cb3.update_ticks()
    plt.show()


from matplotlib.font_manager import FontProperties
fontP = FontProperties()
fontP.set_size('small')
plt.savefig("2body.pdf",prop=fontP, bbox_inches='tight')
print "Average speedup (WH/Mikkola): %.4f" %(np.mean(timing[0])/np.mean(timing[1]))
import os
os.system("open 2body.pdf")
