/**
 * Class written by Zabi94
 * Feb 15, 2018
 * Distributed under MIT license
 * 
 * This class allows the installation of optifine via command line
 * This is not affiliated with Optifine
 */

package zabi.minecraft.ofb.loggers;

import java.io.PrintStream;

public abstract class AbstractLoggerModifier {
	
	private PrintStream oldOutput;
	private PrintStream currentOutput;
	
	public void engage() {
		oldOutput = System.out;
		currentOutput = createNewStream();
		System.setOut(currentOutput);
	}
	
	public void disengage() {
		System.setOut(oldOutput);
		currentOutput.flush();
		currentOutput.close();
	}
	
	public abstract PrintStream createNewStream();
}
