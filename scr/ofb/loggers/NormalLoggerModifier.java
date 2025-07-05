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

public class NormalLoggerModifier extends AbstractLoggerModifier {

	@Override
	public PrintStream createNewStream() {
		return null;
	}
	
	@Override
	public void engage() {
	}
	
	@Override
	public void disengage() {
	}

}
