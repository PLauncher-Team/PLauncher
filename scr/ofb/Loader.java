/**
 * Class written by Zabi94
 * Feb 15, 2018
 * Distributed under MIT license
 * 
 * This class allows the installation of optifine via command line
 * This is not affiliated with Optifine
 */

package zabi.minecraft.ofb;

import java.io.File;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;

import zabi.minecraft.ofb.loggers.AbstractLoggerModifier;
import zabi.minecraft.ofb.loggers.FileLoggerModifier;
import zabi.minecraft.ofb.loggers.NormalLoggerModifier;
import zabi.minecraft.ofb.loggers.VoidLoggerModifier;

public class Loader {

	@SuppressWarnings({ "rawtypes", "unchecked"})
	public static void main(String[] args) {
		if (args.length==0) {
			throw new IllegalArgumentException("No destination directory specified");
		}
		File destDir = new File(args[0]);
		if (!destDir.exists()) {
			throw new IllegalArgumentException("The specified directory doesn't exist: "+args[0]);
		}
		if (destDir.isFile()) {
			throw new IllegalArgumentException("The specified directory is actually a file");
		}
		File file = new File("ofb");
		if (!file.exists() || file.isFile()) throw new IllegalStateException("No \"ofb\" directory found");
		File[] files = file.listFiles(f -> f.exists() && f.isFile() && f.getName().toLowerCase().contains("optifine") && f.getName().toLowerCase().endsWith(".jar"));
		
		AbstractLoggerModifier log_modifier = new FileLoggerModifier();
		
		if (args.length>1){
			if (args[1].toLowerCase().equals("-log=none")) log_modifier=new VoidLoggerModifier();
			else if (args[1].toLowerCase().equals("-log=console")) log_modifier=new NormalLoggerModifier();
		}
		log_modifier.engage();
		
		boolean success = false;
		for (File f:files) {
			try {
				URLClassLoader child = new URLClassLoader(new URL[] {f.toURI().toURL()}, Loader.class.getClassLoader());
				Class classToLoad = Class.forName("optifine.Installer", true, child);
				Method method = classToLoad.getDeclaredMethod("doInstall", File.class);
				method.invoke(null, destDir);
				log_modifier.disengage();
				success=true;
				System.out.println("Optifine installation successful");
				System.exit(0);
			} catch (Exception e) {
				System.err.println(f.getName()+" is not a valid Optifine Jar");
				e.printStackTrace()
				/**
                 * Class written by Zabi94
                 * Feb 15, 2018
                 * Distributed under MIT license
                 * 
                 * This class allows the installation of optifine via command line
                 * This is not affiliated with Optifine
                 */
                
                package zabi.minecraft.ofb;
                
                import java.io.File;
                import java.lang.reflect.Method;
                import java.net.URL;
                import java.net.URLClassLoader;
                
                import zabi.minecraft.ofb.loggers.AbstractLoggerModifier;
                import zabi.minecraft.ofb.loggers.FileLoggerModifier;
                import zabi.minecraft.ofb.loggers.NormalLoggerModifier;
                import zabi.minecraft.ofb.loggers.VoidLoggerModifier;
                
                public class Loader {
                
                	@SuppressWarnings({ "rawtypes", "unchecked"})
                	public static void main(String[] args) {
                		if (args.length==0) {
                			throw new IllegalArgumentException("No destination directory specified");
                		}
                		File destDir = new File(args[0]);
                		if (!destDir.exists()) {
                			throw new IllegalArgumentException("The specified directory doesn't exist: "+args[0]);
                		}
                		if (destDir.isFile()) {
                			throw new IllegalArgumentException("The specified directory is actually a file");
                		}
                		File file = new File("ofb");
                		if (!file.exists() || file.isFile()) throw new IllegalStateException("No \"ofb\" directory found");
                		File[] files = file.listFiles(f -> f.exists() && f.isFile() && f.getName().toLowerCase().contains("optifine") && f.getName().toLowerCase().endsWith(".jar"));
                		
                		AbstractLoggerModifier log_modifier = new FileLoggerModifier();
                		
                		if (args.length>1){
                			if (args[1].toLowerCase().equals("-log=none")) log_modifier=new VoidLoggerModifier();
                			else if (args[1].toLowerCase().equals("-log=console")) log_modifier=new NormalLoggerModifier();
                		}
                		log_modifier.engage();
                		
                		boolean success = false;
                		for (File f:files) {
                			try {
                				URLClassLoader child = new URLClassLoader(new URL[] {f.toURI().toURL()}, Loader.class.getClassLoader());
                				Class classToLoad = Class.forName("optifine.Installer", true, child);
                				Method method = classToLoad.getDeclaredMethod("doInstall", File.class);
                				method.invoke(null, destDir);
                				log_modifier.disengage();
                				success=true;
                				System.out.println("Optifine installation successful");
                				System.exit(0);
                			} catch (Exception e) {
                				System.err.println(f.getName()+" is not a valid Optifine Jar");
                				e.printStackTrace();
                			}
                		}
                		if (!success) {
                			System.err.println("No valid optifine file found");
                			System.exit(-1);
                		}
                	}
                
                }
;
			}
		}
		
		if (!success) {
			System.err.println("No valid optifine file found");
			System.exit(-1);
		}
	}

}
