/* Focused, ROM-free checks against a native CAP32 shared library. */
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <dlfcn.h>
#include "cap32.h"
#include "z80.h"
#include "crtc.h"
#include "asic.h"
int main(int argc,char **argv) {
   assert(argc==2);
   void *lib=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);assert(lib);
   t_CRTC *c=dlsym(lib,"CRTC");t_z80regs *z=dlsym(lib,"z80");
   t_GateArray *ga=dlsym(lib,"GateArray");t_VDU *v=dlsym(lib,"VDU");
   t_flags1 *flags=dlsym(lib,"flags1");t_asic *a=dlsym(lib,"asic");
   void (*init)(void)=dlsym(lib,"crtc_init");void (*reset)(void)=dlsym(lib,"crtc_reset");
   void (*cycle)(int)=dlsym(lib,"crtc_cycle");uint32_t *scale=dlsym(lib,"dwXScale");
   *scale=2;init();
   int widths[]={1,4,8,14};
   for(unsigned i=0;i<4;i++) {
      memset(flags,0,sizeof(*flags));memset(v,0,sizeof(*v));memset(ga,0,sizeof(*ga));reset();
      c->char_count=45;c->line_count=2;c->raster_count=4;c->registers[9]=7;c->hsw=widths[i];
      c->interrupt_sl=20;c->sl_count=99;ga->sl_count=51;z->int_pending=0;
      cycle(1);assert(!z->int_pending);assert(c->raster_interrupt_delay==10);
      cycle(9);assert(!z->int_pending);cycle(1);assert(z->int_pending);assert(a->irq_cause==6);
   }
   puts("PRI: exactly 10 character clocks after HSYNC for widths 1/4/8/14, including GA count 52 coincidence and CRTC counter matching.");
   t_FDC *f=dlsym(lib,"FDC");t_drive *driveA=dlsym(lib,"driveA");t_drive *driveB=dlsym(lib,"driveB");
   void (*seek)(void)=dlsym(lib,"fdc_seek");void (*sense)(void)=dlsym(lib,"fdc_intstat");
   for(int unit=0;unit<2;unit++)for(int motor=0;motor<2;motor++)for(int media=0;media<2;media++){
      t_drive *d=unit?driveB:driveA;memset(f,0,sizeof(*f));d->tracks=media?40:0;d->current_track=28;
      f->motor=motor;f->command[1]=unit;f->command[2]=12;seek();assert(d->current_track==12);sense();
      assert(f->result[0]==(0x20|unit));assert(f->result[1]==12);
      f->command[2]=0;seek();assert(d->current_track==0);sense();assert(f->result[1]==0);
   }
   puts("FDC: seeks to track 12 and track zero work for both drives with motor on/off and media present/absent.");
   return 0;
}
